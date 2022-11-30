import re
from ipaddress import IPv4Interface
from typing import List


class Iface:
    IP_IFACE_UNIT_PREPEND = '8'
    UNNUM_IFACE_UNIT_PREPEND = '9'
    description = None
    is_loopback = False
    is_unnumbered = None
    ip_interfaces = None
    is_subscriber = None
    is_valid = True
    inner_tag = None
    outer_tag = None
    phys_number = None
    phys_name = None
    unit = None
    unit_type = None
    static_routes = None

    def __init__(self, strings: List[str]):
        self.ip_interfaces = []
        self.static_routes = []

        self._parse(strings)
        self._validate()
        self._constructor()

    def _parse(self, strings: List[str]):
        for string in strings:
            if 'interface ' in string:
                interface = re.findall(r'\d/\d/\d', string)
                """
                interface TenGigabitEthernet0/3/0.31993028
                interface Loopback102
                interface Loopback101
                interface GigabitEthernet0
                """
                if 'Loopback' in string:
                    self.is_loopback = True
                    self.is_valid = True

                elif '.' not in string:
                    self.is_valid = False
                    return
                elif not interface:
                    self.is_valid = False
                    return
                else:
                    self.phys_number = interface[0]
                    self.phys_name = string.split()[1]

            if 'shutdown' in string:
                self.is_valid = False
                return

            if 'description' in string:
                description_parts = string.split()[1:]
                self.description = ' '.join(description_parts)
                self._normalize_descr()

            if 'second-dot1q' in string:
                """ encapsulation dot1Q 3199 second-dot1q 3028"""
                encapsulation_parts = string.split()
                self.outer_tag = encapsulation_parts[2]
                self.inner_tag = encapsulation_parts[4]
                self.unit = self.outer_tag.zfill(4) + self.inner_tag.zfill(4)

            if 'ip address ' in string:
                """  ip address 217.151.71.45 255.255.255.252"""
                netw_parts = string.split()
                ip_address = netw_parts[2]
                ip_mask = netw_parts[3]
                ip = IPv4Interface(f'{ip_address}/{ip_mask}')
                self.ip_interfaces.append(ip)
                self.is_unnumbered = False
                self.unit_type = self.IP_IFACE_UNIT_PREPEND

            if 'unnumbered' in string:
                self.is_unnumbered = True
                self.unit_type = self.UNNUM_IFACE_UNIT_PREPEND

            if 'subscriber' in string:
                self.is_subscriber = True

    def _normalize_descr(self):
        self.description = re.sub('"', '', self.description)

    def _constructor(self):
        if not self.is_loopback and self.is_valid:
            self.unit = self.unit_type + self.unit

    def _validate(self):
        if self.is_loopback:
            if not self.ip_interfaces:
                self.is_valid = False
                return

        else:
            if not self.inner_tag:
                self.is_valid = False
                return

            if not self.unit_type:
                self.is_valid = False
                return


class Route:
    phys_name = None
    ip_prefix = None
    next_hop = None

    def __init__(self, route_config: str):
        parts = route_config.split()
        ip_address = parts[2]
        ip_mask = parts[3]
        self.ip_prefix = IPv4Interface(f'{ip_address}/{ip_mask}')

        ip_pattern = r'\d*\.\d*\.\d*\.\d*'
        next_hops = re.findall(ip_pattern, parts[4])

        if next_hops:
            self.next_hop = next_hops[0]
        else:
            self.phys_name = parts[4]


class LocalMigrator:

    def __init__(self, config: str):
        self._ifaces = []
        self._routes = {}

        self._parse_ifaces(config)
        self._parse_routes(config)

    @staticmethod
    def _collapse_to_ranges(inners: List[int]) -> List[list]:
        if len(inners) > 50:
            grid_interval = 10
        else:
            grid_interval = 1

        ranges = []
        for inner in inners:
            if not ranges:
                ranges.append([inner])
            elif inner - prev_inner <= grid_interval:
                ranges[-1].append(inner)
            else:
                ranges.append([inner])
            prev_inner = inner

        return ranges

    def _parse_ifaces(self, config: str):
        current_data = []

        for line in config.splitlines():
            if line.startswith('!'):
                continue

            if line.startswith('interface '):
                if current_data:
                    iface = Iface(current_data)
                    if iface.is_valid:
                        self._ifaces.append(iface)

                    current_data = []

                current_data.append(line)
                continue

            if current_data:
                if not line.startswith(' '):
                    current_data = []
                    continue

                current_data.append(line)

    def _parse_routes(self, config: str):
        for line in config.splitlines():
            if line.startswith('ip route '):
                if 'vrf' in line:
                    continue

                route = Route(line)

                if route.phys_name:
                    if not self._routes.get(route.phys_name):
                        self._routes[route.phys_name] = []
                    self._routes[route.phys_name].append(route)

                else:
                    if not self._routes.get(route.next_hop):
                        self._routes[route.next_hop] = []
                    self._routes[route.next_hop].append(route)

    def config_ip_ifaces(self, phys_number: str, outer_tag: str) -> str:
        ifaces = [
            x for x in self._ifaces
            if x.phys_number == phys_number and x.outer_tag == outer_tag and not x.is_unnumbered
        ]

        output = ''

        for iface in ifaces:
            if not iface.description:
                iface.description = 'NO_DESCRIPTION'

            output += (
                f'set interfaces demux0 unit {iface.unit} description "{iface.description}"\n'
                f'set interfaces demux0 unit {iface.unit} vlan-tags outer {iface.outer_tag}\n'
                f'set interfaces demux0 unit {iface.unit} vlan-tags inner {iface.inner_tag}\n'
            )
            for ip in iface.ip_interfaces:
                output += (
                    f'set interfaces demux0 unit {iface.unit} family inet address {ip}\n'
                )

            # Parse static routes for iface
            ip_networks = [x.network for x in iface.ip_interfaces]

            for network in ip_networks:
                hosts = network.hosts()
                for host in hosts:
                    route = self._routes.get(host.compressed)
                    if not route:
                        continue

                    iface.static_routes.extend(route)

            for route in iface.static_routes:
                output += (
                    f'set routing-options access route {route.ip_prefix} qualified-next-hop {route.next_hop}\n'
                )

            output += f'\n'
        return output

    def config_unnumbered_ifaces(self, phys_number: str, outer_tag: str) -> str:
        lo_networks = []

        for iface in (x for x in self._ifaces if x.is_loopback):
            lo_networks.extend(iface.ip_interfaces)

        no_routes_ifaces = []

        output = ''

        for iface in self._ifaces:
            if not iface.is_unnumbered:
                continue
            if not iface.phys_number == phys_number:
                continue
            if not iface.outer_tag == outer_tag:
                continue
            if not self._routes.get(iface.phys_name):
                no_routes_ifaces.append(iface)
                continue

            # config interface, put into config output
            routes = self._routes.get(iface.phys_name)

            if not iface.description:
                iface.description = 'NO_DESCRIPTION'

            output += (
                f'set interfaces demux0 unit {iface.unit} description "{iface.description}"\n'
                f'set interfaces demux0 unit {iface.unit} vlan-tags outer {iface.outer_tag}\n'
                f'set interfaces demux0 unit {iface.unit} vlan-tags inner {iface.inner_tag}\n'
                f'set interfaces demux0 unit {iface.unit} family inet unnumbered-address lo0.0\n'
            )

            first_cust_route = routes[0].ip_prefix

            gw = ''

            for lo_network in lo_networks:
                if lo_network.network.overlaps(first_cust_route.network):
                    gw = lo_network.ip
                    break

            output += (
                f'set interfaces demux0 unit {iface.unit} family inet unnumbered-address preferred-source-address {gw}\n'
            )

            for route in routes:
                output += (
                    f'set routing-options access-internal route {route.ip_prefix} qualified-next-hop demux0.{iface.unit}\n'
                )

                # Parse static routes for iface
                static_route = self._routes.get(route.ip_prefix.ip.compressed)
                if not static_route:
                    continue

                iface.static_routes.extend(static_route)

            for route in iface.static_routes:
                output += (
                    f'set routing-options access route {route.ip_prefix} qualified-next-hop {route.next_hop}\n'
                )

            output += '\n'

        for iface in no_routes_ifaces:
            output += f'NO ROUTE for {iface.phys_name}\n\n'

        return output

    def config_static_subscribers(self, phys_number: str, outer_tag: str) -> str:
        ip_inners = [
            int(x.inner_tag) for x in self._ifaces
            if x.phys_number == phys_number and x.outer_tag == outer_tag and not x.is_unnumbered and x.is_subscriber
        ]

        unnum_inners = [
            int(x.inner_tag) for x in self._ifaces
            if x.phys_number == phys_number and x.outer_tag == outer_tag and x.is_unnumbered and x.is_subscriber
        ]

        inners_data = {
            'ip': self._collapse_to_ranges(ip_inners),
            'unnum': self._collapse_to_ranges(unnum_inners)
        }

        output = ''

        for iface_type, data in inners_data.items():
            if iface_type == 'ip':
                unit_type = '8'
            else:
                unit_type = '9'
            for obj in data:
                if len(obj) == 1:
                    single_unit = f'{unit_type}{outer_tag.zfill(4)}{str(obj[0]).zfill(4)}'
                    output += f'set system services static-subscribers group DUAL-TAG interface demux0.{single_unit}\n'
                else:
                    unit_start = f'{unit_type}{outer_tag.zfill(4)}{str(obj[0]).zfill(4)}'
                    unit_end = f'{unit_type}{outer_tag.zfill(4)}{str(obj[-1]).zfill(4)}'
                    output += f'set system services static-subscribers group DUAL-TAG interface demux0.{unit_start} to demux0.{unit_end}\n'

        return output
