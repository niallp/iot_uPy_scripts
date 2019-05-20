# This file is executed on every boot (including wake-boot from deepsleep)

# should now try strongest ap it knows about, default to balskG
def do_connect():
    from machine import Pin
    con = Pin(13,Pin.OUT)
    import network
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        con.value(1)
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
        sta_if.active(True)
        if bssid == None:
            sta_if.connect(ssid,pwd)
        else:
            sta_if.connect(ssid,pwd,bssid=bssid)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())
    if sta_if.isconnected():
        con.value(0)

import esp
esp.osdebug(None)
import machine
cause = machine.reset_cause()
print("Reset cause: "+str(cause))
do_connect()
if (cause != machine.DEEPSLEEP_RESET):
    # if wasn't deepsleep wakeup, give user a chance to intervene
    import gc
    import webrepl
    webrepl.start()
    gc.collect()
    from utime import sleep
    print('Ctrl-C to intervene in autostart of logger')
    sleep(120)

exec(open('logger.py').read())
