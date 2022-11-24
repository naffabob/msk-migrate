from tqdm import tqdm
from ipaddress import IPv4Interface

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
    phys_number = None
    outer_tag = None
    inner_tag = None
    description = None
    ip_address = None
    ip_mask = None
    is_unnumbered = None
    is_shutdown = None

    def __init__(self, strings: list):
        for string in strings:
            if 'interface ' in string:
                """interface TenGigabitEthernet0/3/0.31993028"""
                parts = string.split()
                self.phys_number = parts[1].split('.')[0]
            if 'description' in string:
                description_parts = string.split()[1:]
                self.description = ' '.join(description_parts)
            if 'encapsulation' in string:
                """ encapsulation dot1Q 3199 second-dot1q 3028"""
                encapsulation_parts = string.split()
                self.outer_tag = encapsulation_parts[2]
                self.inner_tag = encapsulation_parts[4]
            if 'ip address ' in string:
                """  ip address 217.151.71.45 255.255.255.252"""
                netw_parts = string.split()
                self.ip_address = netw_parts[2]
                self.ip_mask = netw_parts[3]
                self.is_unnumbered = False
            if 'unnumbered' in string:
                self.is_unnumbered = True

    def _parse(self):
        ...

    def generate_config(self):
        ...


class LocalMigrator:
    _routes = {'iface_name': [str or IPv4Interface]}
    _ifaces = []

    def __init__(self, config):
        # with open(f'{hostname}.txt') as f:
        #     self.dev_config = f.read()

        self.dev_config = config
        self._parse_ifaces(self.dev_config)
        self._parse_routes(self.dev_config)

    def _parse_ifaces(self, config: str):
        current_data = []
        for line in config.splitlines():

            if line.startswith('!'):
                continue

            if line.startswith('interface '):
                if current_data:
                    self._ifaces.append(Iface(current_data))
                    current_data = []

                current_data.append(line)
                continue

            if current_data:
                if not line.startswith(' '):
                    if 'interface' in current_data[0]:
                        self._ifaces.append(Iface(current_data))
                    current_data = []
                    continue

                current_data.append(line)

    def _parse_routes(self, config: str):
        ...

    def get_ifaces_by_outer_tag(self, phys_number, outer_tag):
        return [
            x for x in self._ifaces
            if x.phys_number == phys_number and x.outer_tag == outer_tag
        ]

    def config_ip_interfaces(self, phys_number, outer_tag, data: dict) -> str:
        ...

    def config_unnumbered_interfaces(self,phys_number, outer_tag, data: dict) -> str:
        ...
