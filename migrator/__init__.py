import re
from ipaddress import IPv4Interface

from tqdm import tqdm

from cisco_executor import Account, CiscoExecutor
from data_sets import up_tags_20


class DeviceMigrator:
    def __init__(self, username, password, hostname, interface, outer_tag):
        self.account = Account(username=username, password=password)
        self.hostname = hostname
        self.interface = interface
        self.sub_interface = '.'.join([interface, outer_tag])
        self.interfaces_data = {
            'ip': [],
            'unnumbered': [],
            'dummy': [],
        }

        self.ex = CiscoExecutor(account=self.account, hostname=hostname, connect=True)

    def get_tags(self):
        print('get_tags proccess')
        output = self.ex.cmd(f'show interfaces description | include {self.sub_interface}.*.up.*.up')
        up_sub_interfaces = [line.split()[0] for line in tqdm(output.splitlines())
                             if ('FREE' not in line)
                             and ('show' not in line)
                             and (self.hostname not in line)]

        up_tags = [_.split('.')[1] for _ in up_sub_interfaces]

        # self.ex.close()
        return up_tags

    def get_ip_iface_data(self, data: str) -> dict:
        interface = {}

        for line in data.splitlines():
            if 'description' in line:
                description_parts = line.split()[1:]
                interface['descr'] = ' '.join(description_parts)
            if 'encapsulation' in line:
                encapsulation_parts = line.split()
                interface['outer'] = encapsulation_parts[2]
                interface['inner'] = encapsulation_parts[4]
            if 'ip address ' in line:
                netw_parts = line.split()
                interface['ip'] = netw_parts[2]
                interface['mask'] = netw_parts[3]
        return interface

    def get_unnumbered_iface_data(self, data: str) -> dict:
        interface = {}

        for line in data.splitlines():
            if 'description' in line:
                description_parts = line.split()[1:]
                interface['descr'] = ' '.join(description_parts)
            if 'encapsulation' in line:
                encapsulation_parts = line.split()
                interface['outer'] = encapsulation_parts[2]
                interface['inner'] = encapsulation_parts[4]
            if 'ip route ' in line:
                netw_parts = line.split()
                interface['ip'] = netw_parts[2]
                interface['mask'] = netw_parts[3]
        return interface

    def get_dummy_iface_data(self, data) -> dict:
        interface = {
            'descr': 'DUMMY_IFACE',
            'data': data,
        }
        return interface

    def get_interfaces_data(self) -> (dict):
        print(f'get_interfaces_data proccess from {self.hostname}')

        # up_tags = self.get_tags()
        up_tags = up_tags_20[-10:]
        for tag in tqdm(up_tags):
            interface_output = self.ex.cmd(f'show startup-config | section {self.interface}.{tag}$')

            if 'ip address' in interface_output:
                ip_ifaces = self.get_ip_iface_data(interface_output)
                self.interfaces_data['ip'].append(ip_ifaces)
            elif 'unnumbered' in interface_output:
                unnum_ifaces = self.get_unnumbered_iface_data(interface_output)
                self.interfaces_data['unnumbered'].append(unnum_ifaces)
            else:
                dummy_iface = self.get_dummy_iface_data(interface_output)
                self.interfaces_data['dummy'].append(dummy_iface)
        print(
            f"""
            interfaces
            IP: {len(self.interfaces_data['ip'])}
            Unnumbered: {len(self.interfaces_data['unnumbered'])}
            Dummy: {len(self.interfaces_data['dummy'])}
            """
        )

        return self.interfaces_data

    def generate_config_ip_interfaces(self) -> str:
        ifaces = self.interfaces_data['ip']
        print(f'IP interfaces: {len(ifaces)}')

        output = ''
        for iface in ifaces:
            if not iface.get('descr'):
                iface['descr'] = 'NO_DESCRIPTION'

            unit_outer = iface['outer'].zfill(4)
            unit_inner = iface['inner'].zfill(4)

            ip = IPv4Interface((iface['ip'], iface['mask']))
            ip_prefix = ip.with_prefixlen

            output += f"""
set interfaces demux0 unit 8{unit_outer}{unit_inner} description "{iface['descr']}"
set interfaces demux0 unit 8{unit_outer}{unit_inner} vlan-tags outer {iface['outer']}
set interfaces demux0 unit 8{unit_outer}{unit_inner} vlan-tags inner {iface['inner']}
set interfaces demux0 unit 8{unit_outer}{unit_inner} family inet address {ip_prefix}"""
        return output

    def generate_config_unnumbered_interfaces(self):
        """"
        set interfaces demux0 unit 1501368 description "--(CUST-CORP)- OOO Artiko-group rt#977466"
        set interfaces demux0 unit 1501368 vlan-tags outer 1501
        set interfaces demux0 unit 1501368 vlan-tags inner 368
        set interfaces demux0 unit 1501368 family inet unnumbered-address lo0.0
        set interfaces demux0 unit 1501368 family inet unnumbered-address preferred-source-address 79.111.242.1
        set routing-options access-internal route 79.111.242.126/32 qualified-next-hop demux0.1501368
        """
        ifaces = self.interfaces_data['unnumbered']
        print(f'Unnumbered interfaces: {len(ifaces)}')

        output = ''
        for iface in ifaces:
            octets = iface['ip'].split('.')
            octets[3] = '1'
            gw = '.'.join(octets)

            if not iface.get('descr'):
                iface['descr'] = 'NO_DESCRIPTION'

            unit_outer = iface['outer'].zfill(4)
            unit_inner = iface['inner'].zfill(4)

            ip = IPv4Interface((iface['ip'], iface['mask']))
            ip_with_prefixlen = ip.with_prefixlen

            output += f"""
set interfaces demux0 unit 9{unit_outer}{unit_inner} description "{iface['descr']}"
set interfaces demux0 unit 9{unit_outer}{unit_inner} vlan-tags outer {iface['outer']}
set interfaces demux0 unit 9{unit_outer}{unit_inner} vlan-tags inner {iface['inner']}
set interfaces demux0 unit 9{unit_outer}{unit_inner} family inet unnumbered-address lo0.0
set interfaces demux0 unit 9{unit_outer}{unit_inner} family inet unnumbered-address preferred-source-address {gw}
set routing-options access-internal route {ip_with_prefixlen} qualified-next-hop demux0.9{unit_outer}{unit_inner}"""

        return output

    def show_dummy_interfaces(self):
        ifaces = self.interfaces_data['dummy']
        print(f'Dummy interfaces: {len(ifaces)}')

        if not ifaces:
            return 'No dummy interfaces'
        return ifaces

    def generate_config_shutdown_interfaces(self):
        pass


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
