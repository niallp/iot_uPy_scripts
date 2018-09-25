# This file is executed on every boot (including wake-boot from deepsleep)

def do_connect():
    import network
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('balskG', '')
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

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
    sleep(120)

exec(open('logger.py').read())
