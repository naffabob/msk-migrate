config3 = """! Cisco IOS Software, IOS-XE Software (X86_64_LINUX_IOSD-ADVENTERPRISEK9-M)
! 
! Image: Software: X86_64_LINUX_IOSD-ADVENTERPRISEK9-M
!
cinfug
config
silly config
!
interface TenGigabitEthernet0/0/0.300125
 description -- test-user
 encapsulation dot1Q 300 second-dot1q 125
 ip address 176.192.124.13 255.255.255.252
 no ip redirects
 no ip unreachables
 ip verify unicast source reachable-via rx
 shutdown
 service-policy type control INTERFACE_SUBSCRIBERS-UFO
 ip subscriber interface
!
interface TenGigabitEthernet0/0/0.300671
 description -- test-user
 encapsulation dot1Q 300 second-dot1q 671
 ip address 46.16.177.149 255.255.255.252
 no ip redirects
 no ip unreachables
 ip verify unicast source reachable-via rx
 shutdown
 service-policy type control INTERFACE_SUBSCRIBERS
 ip subscriber interface
!
interface TenGigabitEthernet0/0/0.300673
 description --(CUST-CORP)- 20160506120000 test-user
 encapsulation dot1Q 300 second-dot1q 673
 ip address 46.16.177.145 255.255.255.252
 no ip redirects
 no ip unreachables
 ip verify unicast source reachable-via rx
 service-policy type control INTERFACE_SUBSCRIBERS
 ip subscriber interface
!
interface TenGigabitEthernet0/0/0.300676
 description -- FREE_test-user
 encapsulation dot1Q 300 second-dot1q 676
 ip address 46.16.177.177 255.255.255.248
 no ip redirects
 no ip unreachables
 ip verify unicast source reachable-via rx
 shutdown
 service-policy type control INTERFACE_SUBSCRIBERS
 ip subscriber interface
!
interface TenGigabitEthernet0/3/0.362882
 description --(CUST-CORP)- 20211008105549 test-user --
 encapsulation dot1Q 362 second-dot1q 882
 ip unnumbered Loopback101
 no ip redirects
 no ip unreachables
 ip verify unicast source reachable-via rx
 service-policy type control INTERFACE_SUBSCRIBERS
 ip subscriber interface
!
interface TenGigabitEthernet0/3/0.362883
 description --(CUST-CORP)- 20200408102726 test-user --
 encapsulation dot1Q 362 second-dot1q 883
 ip unnumbered Loopback101
 no ip redirects
 no ip unreachables
 ip verify unicast source reachable-via rx
 service-policy type control INTERFACE_SUBSCRIBERS
 ip subscriber interface
!
config1
config1
config1
config1
"""

config1 = """interface TenGigabitEthernet0/3/0.1501363
 description testuser
 encapsulation dot1Q 1501 second-dot1q 363
 ip address 217.151.72.41 255.255.255.252
 no ip redirects
 no ip unreachables
 no ip proxy-arp
 ip verify unicast source reachable-via rx
 service-policy type control INTERFACE_SUBSCRIBERS
 ip subscriber interface
!
interface TenGigabitEthernet0/3/0.1501364
 description --(CUST-CORP)- 20170329115201 testuser --
 encapsulation dot1Q 1501 second-dot1q 364
 ip unnumbered Loopback101
 no ip redirects
 no ip unreachables
 ip verify unicast source reachable-via rx
 service-policy type control INTERFACE_SUBSCRIBERS
 ip subscriber interface
!
interface TenGigabitEthernet0/3/0.1501365
 description testuser
 encapsulation dot1Q 1501 second-dot1q 365
 ip address 185.50.138.81 255.255.255.252
 no ip redirects
 no ip unreachables
 no ip proxy-arp
 ip verify unicast source reachable-via rx
 service-policy type control INTERFACE_SUBSCRIBERS
 ip subscriber interface
!
interface TenGigabitEthernet0/3/0.1501366
 description testuser
 encapsulation dot1Q 1501 second-dot1q 366
 ip unnumbered Loopback101
 ip verify unicast source reachable-via rx
!
configconfig
configconfig
"""