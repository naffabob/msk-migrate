from migrator import DeviceMigrator, LocalMigrator
from getpass import getpass
from test_data import config1, config3


def use_device_migrate():
    username = 'testuser'
    password = getpass('Password: ')
    hostname = input('Hostname: ')
    interface = input('Interface (ex. 0/2/0): ')
    outer_tag = input('Outer_tag (ex. 364): ')

    dm = DeviceMigrator(username, password, hostname, interface, outer_tag)

    dm.get_interfaces_data()
    print(dm.generate_config_ip_interfaces())
    print(dm.generate_config_unnumbered_interfaces())
    print(dm.show_dummy_interfaces())


if __name__ == '__main__':
    lm = LocalMigrator(config3)

