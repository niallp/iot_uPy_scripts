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
        bssid = None
        pwd = None
        nets = sta_if.scan()
        nets.sort(key=lambda net: net[3], reverse=True)     # strongest first
        from boardCfg import known_nets
        for net in nets:
            ssid = net[0].decode('utf-8')
            if ssid in known_nets:
                bssid = net[1]
                pwd = known_nets[ssid]['pwd']
                break
            else:
                print(ssid+" is unknown")
        print('connecting to network '+ssid)
        if bssid == None:
            sta_if.connect(ssid,pwd)
        else:
            sta_if.connect(ssid,pwd,bssid=bssid)
        while (not sta_if.isconnected() and retry < maxRetry):
            retry = retry + 1
            sleep_ms(500)
    print('network config:', sta_if.ifconfig())
    return sta_if.isconnected()


import esp
esp.osdebug(None)
import machine
dbgSel = machine.Pin(14,machine.Pin.IN,machine.Pin.PULL_UP)
if (dbgSel.value() == 0):   #cause != machine.DEEPSLEEP_RESET):
    # give user a chance to intervene
    do_connect(10)
    import gc
    import webrepl
    webrepl.start()
    gc.collect()
else:
    if (do_connect(4)):
        exec(open('logger.py').read())
