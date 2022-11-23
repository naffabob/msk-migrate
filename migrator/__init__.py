from tqdm import tqdm
from ipaddress import IPv4Interface

from cisco_executor import Account, CiscoExecutor
from data_sets import up_tags_20


class Migrator:
    def __init__(self):
        self.account = Account(username='nbobkova')
        self.hostname = input('Hostname: ')
        self.interface = input('Interface (ex. 0/2/0): ')
        self.outer_tag = input('Outer_tag (ex. 364): ')
        self.sub_interface = '.'.join([self.interface, self.outer_tag])
        self.interfaces_data = {
            'ip': [],
            'unnumbered': [],
            'dummy': [],
        }

        self.ex = CiscoExecutor(account=self.account, hostname=self.hostname, connect=True)

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
            interface_output = self.ex.cmd(f'show startup-config | section {self.interface}.{tag}$', timer=8)

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
