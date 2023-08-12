# This file is executed on every boot (including wake-boot from deepsleep)

# should now try strongest ap it knows about, default to balskG

def do_connect(maxRetry):
    retry = 0
    import network
    from utime import sleep_ms
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    if not sta_if.isconnected():
        # first try cached connection
        sta_if.connect()
        sleep_ms(200)
        if sta_if.isconnected():
            print('\n(cached)network config:', sta_if.ifconfig())
            return True
        else:
            print('\ncached network failed, scanning')
        # if didn't work 1st go then scan and try list
        sta_if.active(True)
        bssid = None
        pwd = None
        try: 
            nets = sta_if.scan()
        except OSError:
            return False
        print('{} nets found'.format(len(nets)))
        nets.sort(key=lambda net: net[3], reverse=True)     # strongest first
        from netConfig import known_nets
        for net in nets:
            ssid = net[0].decode('utf-8')
            if ssid in known_nets:
                bssid = net[1]
                import netConfig
                netConfig.RSSI = net[3]
                print("RSSI: ", netConfig.RSSI)

                if bssid == b'\xc0J\x00,\xb1\x8d':
                    print('skip bssid '+str(bssid))
                else:
                    pwd = known_nets[ssid]['pwd']
                    break
            else:
                print(ssid+" is unknown")
        print('connecting to network '+ssid+' BSSID: '+str(bssid))
        if bssid == None:
            sta_if.connect(ssid,pwd)
        else:
            sta_if.connect(ssid,pwd,bssid=bssid)
        while (not sta_if.isconnected() and retry < maxRetry):
            retry = retry + 1
            print('retry {}'.format(retry))
            sleep_ms(500)
    print('network config:', sta_if.ifconfig())
    return sta_if.isconnected()



import esp
esp.osdebug(None)
import machine
dbgSel = machine.Pin(14,machine.Pin.IN,machine.Pin.PULL_UP)
if (dbgSel.value() == 0):   #cause != machine.DEEPSLEEP_RESET):
    # give user a chance to intervene
    print('Starting debug mode');
    do_connect(99)
    import gc
    import webrepl
    webrepl.start()
    gc.collect()
else:
    #input("keyboard input: ")
        
    try:
        if (not do_connect(30)):   # network failed, go back to sleep for 5 minutes
            import netConfig
            netConfig.wifiConnected = False

            print("failed do_connect: " + str(netConfig.wifiConnected))

            #machine.deepsleep(60000)
        else:
            
            import netConfig
            print("connected: " + str(netConfig.wifiConnected))
            netConfig.wifiConnected = True
            print("passed doconnect: " + str(netConfig.wifiConnected))

            print('starting')
            
            
    except:
        import netConfig
        print("exceptions: doconnect: " + str(netConfig.wifiConnected))
        netConfig.wifiConnected = False
        print("exception: doconnect, wifi should be False -> " + str(netConfig.wifiConnected))

        print('starting from exception')
