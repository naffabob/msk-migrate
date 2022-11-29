from migrator import LocalMigrator


def use_local_migrate() -> str:
    hostname = input('Hostname: ')
    interface = input('Interface (ex. 0/2/0): ')
    outer_tag = input('Outer_tag (ex. 364): ')

    output = ''

    lm = LocalMigrator(hostname=hostname)
    output += lm.config_ip_ifaces(interface, outer_tag)
    output += lm.config_unnumbered_ifaces(interface, outer_tag)
    output += lm.config_static_subscribers(interface, outer_tag)
    if not output:
        return f'No current active interfaces for outer: {interface}.{outer_tag}'

    return output


if __name__ == '__main__':
    print(use_local_migrate())
