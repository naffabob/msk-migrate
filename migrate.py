from migrator import LocalMigrator, CONFIG_DIR


def use_local_migrate() -> str:
    try:
        hostname = input('Hostname: ')
        interface = input('Interface (ex. 0/2/0): ')
        outer_tag = int(input('Outer_tag (ex. 364): '))
    except KeyboardInterrupt:
        print('\nTry again later')
        quit()
    except TypeError:
        print('\n TypeError (str/int)')
        quit()

    try:
        with open(f'{CONFIG_DIR}{hostname}.ti.ru') as f:
            dev_config = f.read()
    except FileNotFoundError:
        print('No such config file.')
        quit()

    output = ''

    lm = LocalMigrator(dev_config)
    output += lm.config_ip_ifaces(interface, outer_tag)
    output += lm.config_unnumbered_ifaces(interface, outer_tag)
    output += lm.config_static_subscribers(interface, outer_tag)
    output += lm.config_cisco_shutdown(interface, outer_tag)
    if not output:
        return f'No current active interfaces for outer: {interface}.{outer_tag}'

    return output


if __name__ == '__main__':
    print(use_local_migrate())
