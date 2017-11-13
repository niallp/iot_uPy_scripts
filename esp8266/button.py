# pub/sub button LED gadget for stage communication
from machine import Pin
import time
import machine
import os
from umqtt_simple import MQTTClient

def sub_cb(topic, msg):
    global grn
    grn.value(int(msg))

# account for voltage divider of 100k over 22k on Vinput: tweaked to calibrate
def vin_str(adc,scl):
    acc = 0
    for r in range(10):     # average over 10 in case of noise
        acc += adc()
    milliVolts = ((acc-25)*scl) // 1024
    return str(milliVolts // 1000) + "." + "{0:0>3}".format(milliVolts % 1000)

mch = os.uname().machine
uniq = machine.unique_id()
if 'ESP8266' in mch:
    if uniq[0] == 0x5d:
        brdName = 'esp12a'
        adcScl = 548
    else:
        brdName = 'esp12b'
        adcScl = 531
elif 'LaunchPad' in mch:
    if uniq==b'TJ\x16)\xc91':
        brdName = 'lp1'
    else:
        brdName = 'lp2'
    print("Launchpad not supported with this version")
    raise SystemExit
else:
    print("board not recognized only")
    raise SystemExit

#setup 
grn = Pin(13, mode=Pin.OUT)
butt = Pin(0, Pin.IN, Pin.PULL_UP)
adc = machine.ADC(0)
vin = adc.read

#open client 
c = MQTTClient(brdName,"mqtt")
c.set_callback(sub_cb)
c.connect()
c.subscribe(b"led")

time.sleep(1)

prev_butt = butt.value()

while True:
    c.check_msg()
    if prev_butt != butt.value():
        c.publish(b"led",str(butt.value()))
        c.publish(brdName+"/vin",vin_str(vin,adcScl))
    prev_butt = butt.value()
    time.sleep_ms(1000)

c.disconnect()
