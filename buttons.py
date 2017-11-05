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
    p_usr.value(0)
    pubCount += 1
    p_usr.value(1)

# returns temperature in degree C from LM35 as string
def lm35C_str(adc):
    milliVolts = (adc()*1100*4) // (3 * 4096)
    return str(milliVolts // 10) + "." + str(milliVolts % 10)

# account for voltage divider of 115k over 56k on Vinput
def vin_str(adc):
    milliVolts = (adc()*171*1100*4) // (3*56*4096)
    return str(milliVolts // 1000) + "." + str(milliVolts % 1000)

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
rtc.alarm(time=60000, repeat=True)

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
