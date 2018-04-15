import os
import machine
import pycom

pycom.heartbeat(False)
pycom.rgbled(0x00000f)
uart = machine.UART(0, 115200)
os.dupterm(uart)
pycom.rgbled(0)

if machine.reset_cause() != machine.SOFT_RESET:
    from boardCfg import known_nets
    import wifi 
    wifi.connect(known_nets)
