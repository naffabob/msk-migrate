import re
from ipaddress import IPv4Interface


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

    def __init__(self, strings: list):
        self.ip_interfaces = []

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
                ip = IPv4Interface((ip_address, ip_mask))
                self.ip_interfaces.append(ip)
                self.is_unnumbered = False
                self.unit_type = self.IP_IFACE_UNIT_PREPEND

            if 'unnumbered' in string:
                self.is_unnumbered = True
                self.unit_type = self.UNNUM_IFACE_UNIT_PREPEND

            if 'subscriber' in string:
                self.is_subscriber = True

        self._validate()
        self._constructor()

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

    def __init__(self, route_config: str):
        parts = route_config.split()
        ip_address = parts[2]
        ip_mask = parts[3]
        self.ip_prefix = IPv4Interface((ip_address, ip_mask))
        self.phys_name = parts[4]


class LocalMigrator:
    _ifaces = []
    _routes = {}

    def __init__(self, hostname):
        with open(f'{hostname}.txt') as f:
            self.dev_config = f.read()

        self._parse_ifaces(self.dev_config)
        self._parse_routes(self.dev_config)

    @staticmethod
    def _collapse_to_ranges(inners: list) -> list:
        if len(inners) > 50:
            grid_interval = 10
        else:
            grid_interval = 1

        i = 0
        end = 0
        inners_aggregated = []

        while i < len(inners) - 1:
            if inners[i + 1] - inners[i] <= grid_interval:
                start = inners[i]
                while True:
                    i += 1
                    if inners[i] == inners[-1]:
                        end = inners[-1]
                        break
                    elif inners[i + 1] - inners[i] <= grid_interval:
                        continue
                    else:
                        end = inners[i]
                        i += 1
                        break
                inners_aggregated.append((str(start), str(end)))

            else:
                inners_aggregated.append(str(inners[i]))
                i += 1

        return inners_aggregated

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
            if line.startswith('ip route ') and 'thernet' in line:
                route = Route(line)
                if not self._routes.get(route.phys_name):
                    self._routes[route.phys_name] = []
                self._routes[route.phys_name].append(route)

    def config_ip_ifaces(self, phys_number, outer_tag) -> str:
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
            output += f'\n'
        return output

    def config_unnumbered_ifaces(self, phys_number, outer_tag) -> str:
        ifaces = [
            x for x in self._ifaces
            if x.phys_number == phys_number and x.outer_tag == outer_tag and x.is_unnumbered
        ]

        lo_networks = []

        for iface in (x for x in self._ifaces if x.is_loopback):
            lo_networks.extend(iface.ip_interfaces)

        output = ''

        for iface in ifaces:

            routes = self._routes.get(iface.phys_name)

            if not routes:
                output += f'NO ROUTE for {iface.phys_name}\n'
                continue

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

            output += '\n'

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
                if isinstance(obj, tuple):
                    unit_start = f'{unit_type}{outer_tag.zfill(4)}{obj[0].zfill(4)}'
                    unit_end = f'{unit_type}{outer_tag.zfill(4)}{obj[1].zfill(4)}'
                    output += f'set system services static-subscribers group DUAL-TAG interface demux0.{unit_start} to demux0.{unit_end}\n'
                else:
                    single_unit = f'{unit_type}{outer_tag.zfill(4)}{obj.zfill(4)}'
                    output += f'set system services static-subscribers group DUAL-TAG interface demux0.{single_unit}\n'

        return output
