# pub/sub button LED gadget for stage communication
from machine import Pin
import time
import machine
import os
import wipy
from simple import MQTTClient

def sub_cb(topic, msg):
    global grn, yel
    grn.value(int(int(msg)//10))
    yel.value(int(int(msg)%10))

mch = os.uname().machine
uniq = machine.unique_id()
if 'LaunchPad' in mch:
    if uniq==b'TJ\x16)\xc91':
        brdName = 'lp1'
    else:
        brdName = 'lp2'
else:
    print("LaunchPad only for now")
    raise SystemExit

#setup 
wipy.heartbeat(False)
red = Pin('GP9', mode=Pin.OUT)
yel = Pin('GP10', mode=Pin.OUT)
grn = Pin('GP11', mode=Pin.OUT)
sw2 = Pin('GP22', mode=Pin.IN)
sw3 = Pin('GP13', mode=Pin.IN)

#open client 
c = MQTTClient(brdName,"pogo2")
c.set_callback(sub_cb)
c.connect()
c.subscribe(b"leds")

time.sleep(1)

prev_sw2 = sw2.value()
prev_sw3 = sw3.value()

while True:
    c.check_msg()
    if prev_sw2 != sw2.value() or prev_sw3 != sw3.value():
        c.publish(b"leds",str(sw2.value()+10*sw3.value()))
    prev_sw2 = sw2.value()
    prev_sw3 = sw3.value()
    time.sleep_ms(500)

c.disconnect()
