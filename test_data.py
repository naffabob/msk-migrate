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
interface TenGigabitEthernet0/3/0.3643604
 description --(CUST-CORP)- 20200629110751 test-user
 encapsulation dot1Q 364 second-dot1q 3604
 ip unnumbered Loopback101
 no ip redirects
 no ip unreachables
 ip verify unicast source reachable-via rx
 service-policy type control INTERFACE_SUBSCRIBERS
 ip subscriber interface
 interface TenGigabitEthernet0/3/0.36436
 description --(CUST-CORP)- 20150201120000 test-user
 encapsulation dot1Q 364 second-dot1q 36
 ip address 93.90.42.213 255.255.255.248
 no ip redirects
 no ip unreachables
 no ip proxy-arp
 ip verify unicast source reachable-via rx
 service-policy type control INTERFACE_SUBSCRIBERS
 ip subscriber interface
!
interface TenGigabitEthernet0/3/0.34995
 description --(CUST-CORP)- 20171124105506 test-user
 encapsulation dot1Q 349 second-dot1q 95
 ip unnumbered Loopback101
 no ip redirects
 no ip unreachables
 ip verify unicast source reachable-via rx
 service-policy type control INTERFACE_SUBSCRIBERS
 ip subscriber interface
!
interface TenGigabitEthernet0/3/0.3643860
 description --(CUST-CORP)- 20171204143000 test-user
 encapsulation dot1Q 364 second-dot1q 3860
 ip unnumbered Loopback101
 no ip redirects
 no ip unreachables
 ip verify unicast source reachable-via rx
 service-policy type control INTERFACE_SUBSCRIBERS
 ip subscriber interface
!
interface TenGigabitEthernet0/3/0.31993033
 description --(CUST-CORP)- test-user
 encapsulation dot1Q 3199 second-dot1q 3033
!
interface GigabitEthernet0
 vrf forwarding Mgmt-intf
 no ip address
 shutdown
 negotiation auto
!
config1
!
ip route 79.111.246.186 255.255.255.255 TenGigabitEthernet0/3/0.34995 tag 12714711
ip route 77.94.171.128 255.255.255.248 185.50.139.42 name Riga-Land
ip route 77.94.171.128 255.255.255.248 77.75.0.250 2 name Riga-Land-reserv
ip route 79.111.242.2 255.255.255.255 TenGigabitEthernet0/3/0.363400
ip route 79.111.242.3 255.255.255.255 TenGigabitEthernet0/3/0.363401
ip route 79.111.242.13 255.255.255.255 TenGigabitEthernet0/3/0.363401
ip route 79.111.242.4 255.255.255.255 TenGigabitEthernet0/3/0.363402
ip route 79.111.242.5 255.255.255.255 TenGigabitEthernet0/3/0.1500422
ip route 79.111.242.41 255.255.255.255 TenGigabitEthernet0/3/0.3643871
ip route 79.111.242.165 255.255.255.255 TenGigabitEthernet0/3/0.3643604
ip route 79.111.246.190 255.255.255.255 TenGigabitEthernet0/3/0.3643860
ip route 79.111.246.191 255.255.255.248 TenGigabitEthernet0/3/0.3643860
!
config1
config1
"""