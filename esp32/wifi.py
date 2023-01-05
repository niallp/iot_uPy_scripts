def connect(known_nets):
    import machine
    from pycom import rgbled
    from network import WLAN
    from time import sleep
    wl = WLAN()
    wl.mode(WLAN.STA)
    original_ssid = wl.ssid()
    original_auth = wl.auth()
    if original_ssid == None:
        original_ssid = 'fipy'

    rgbled(0x0f0000)
    print("Scanning for known wifi nets")
     
    available_nets = wl.scan()
    rgbled(0)
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
            print("Trying to connect to "+net_to_use)
            wl.connect(net_to_use,timeout=10000)
        else:
            sec = [e.sec for e in available_nets if e.ssid == net_to_use][0]
            wl.connect(net_to_use, (sec, pwd), timeout=10000)
        while not wl.isconnected():
            machine.idle() # save power while waiting
        rgbled(0x000f00)
        sleep(1)
        print('Connected to '+net_to_use+' with IP address: '+ wl.ifconfig()[0])
        rgbled(0)

    except Exception as e:
        print("Exception: "+str(e))
        print("Failed to connect to any known network, going into AP mode")
        wl.init(mode=WLAN.AP, ssid=original_ssid, auth=original_auth, channel=6, antenna=WLAN.INT_ANT)
