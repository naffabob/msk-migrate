from migrator import Migrator

if __name__ == '__main__':

    m = Migrator()

    m.get_interfaces_data()
    print(m.generate_config_ip_interfaces())
    print(m.generate_config_unnumbered_interfaces())
    print(m.show_dummy_interfaces())

    choice = input().lower()
    if choice in {'yes', 'y', 'ye', ''}:
        print('ok')
        #print(m.generate_config_shutdown_interfaces())
    elif choice in {'no', 'n'}:
        quit(1)
    else:
        print("Please respond with 'yes' or 'no'")

