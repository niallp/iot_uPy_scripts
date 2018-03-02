# This file is executed on every boot (including wake-boot from deepsleep)

def do_connect():
    import network
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
if (cause == machine.PWRON_RESET) or (cause == machine.DEEPSLEEP_RESET):
    exec(open('logger.py').read())
else:
    import gc
    import webrepl
    webrepl.start()
    gc.collect()
