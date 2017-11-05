# basic data logger using WiPy
# fork back to wipy
# Niall Parker, 7apr2016
from machine import Pin
import socket
import time
import machine
import os
import wipy

import mqtt

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

# for periodic publishing
def publish_handler(rtc_o):
    global pubCount
    red.value(1)
    pubCount += 1
    red.value(0)

#setup 
wipy.heartbeat(False)
red = Pin('GP9', mode=Pin.OUT)
yel = Pin('GP10', mode=Pin.OUT)
grn = Pin('GP11', mode=Pin.OUT)
sw2 = Pin('GP22', mode=Pin.IN)
sw3 = Pin('GP13', mode=Pin.IN)

pubCount = 0
nextCount = pubCount

# setup RTC interrupt handler to publish once every period
rtc = machine.RTC()
rtc_i = rtc.irq(trigger=machine.RTC.ALARM0, handler=publish_handler, wake=machine.IDLE)
rtc.alarm(time=2000, repeat=True)

#open socket and send first message
addr = socket.getaddrinfo("pogo2",1883)[0][4]
s = socket.socket()
s.connect(addr)
s.send(mqtt.connect(brdName))

time.sleep(1)

s.send(mqtt.pub(brdName,b"starting:"+str(pubCount)))

while True:
    s.send(mqtt.pub(brdName+"/iter",str(pubCount)))
    s.send(mqtt.pub(brdName+"/sw2",str(sw2.value())))
    s.send(mqtt.pub(brdName+"/sw3",str(sw3.value())))
    nextCount += 1
    while nextCount > pubCount:
        machine.idle()
