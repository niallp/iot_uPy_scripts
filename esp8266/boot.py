# This file is executed on every boot (including wake-boot from deepsleep)

# should now try strongest ap it knows about

def do_connect(maxRetry):
    retry = 0
    import network
    from utime import sleep_ms
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    sta_if = network.WLAN(network.STA_IF)
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

# try ntptime if time not set or 1 day passed since last time synched
# note only try if we have wifi connection
if netConfig.wifiConnected:
    import time
    import ustruct
    rtc = machine.RTC()
    if len(rtc.memory()) == 0:
        rtcSetTime = 0
    else:
        rtcSetTime = ustruct.unpack('L',rtc.memory())[0]
    now = time.time()
    if now < 754471188 or rtcSetTime == 0 or now-rtcSetTime > 86400:
        print('need to resync time')
        import ntptime
        ntptime.host = "0.ca.pool.ntp.org"
        try:
            ntptime.settime()
            print("ntptime worked")
            rtc.memory(ustruct.pack('L',time.time()))
        except:
            print("ntptime error ...")
    else:
        print("skipping NTP sync")
else:
    print("can't sync time, no network")
