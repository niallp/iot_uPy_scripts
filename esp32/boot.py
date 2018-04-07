import os
import machine

uart = machine.UART(0, 115200)
os.dupterm(uart)

known_nets = {
    'balskG': {'pwd': None},
    'exceptional': {'pwd': None},
    'Community Hall': {'pwd': None},
    'rcmsar20': {'pwd': None, 'wlan_config': ('192.168.20.51', '255.255.255.0', '192.168.20.1', '192.168.20.1')},
    'Port Browning Marina': {'pwd': 'cra175tb34'} 
}

if machine.reset_cause() != machine.SOFT_RESET:
    from network import WLAN
    wl = WLAN()
    wl.mode(WLAN.STA)
    original_ssid = wl.ssid()
    original_auth = wl.auth()

    print("Scanning for known wifi nets")
     
    available_nets = wl.scan()
    nets = frozenset([e.ssid for e in available_nets])

    known_nets_names = frozenset([key for key in known_nets])
    net_to_use = list(nets & known_nets_names)
    try:
        net_to_use = net_to_use[0]
        net_properties = known_nets[net_to_use]
        pwd = net_properties['pwd']
        if 'wlan_config' in net_properties:
            wl.ifconfig(config=net_properties['wlan_config'])
        if pwd == None:
            wl.connect(net_to_use,timeout=10000)
        else:
            sec = [e.sec for e in available_nets if e.ssid == net_to_use][0]
            wl.connect(net_to_use, (sec, pwd), timeout=10000)
        while not wl.isconnected():
            machine.idle() # save power while waiting
        print('Connected to '+net_to_use+' with IP address: '+ wl.ifconfig()[0])

    except Exception as e:
        print("Failed to connect to any known network, going into AP mode")
        wl.init(mode=WLAN.AP, ssid=original_ssid, auth=original_auth, channel=6, antenna=WLAN.INT_ANT)