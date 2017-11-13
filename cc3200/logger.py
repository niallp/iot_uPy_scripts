# basic data logger using WiPy
# fork back to wipy
# Niall Parker, 7apr2016
from machine import Pin
import socket
import time
import machine
import os
import wipy

from umqtt_simple import MQTTClient

mch = os.uname().machine
uniq = machine.unique_id()
if 'WiPy' in mch:
    brdName = 'wipy'
else:
    print("wipy only now")
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
p_usr = Pin('GP16', mode=Pin.OUT)
p_usr.value(1)		# turn off user LED

adc = machine.ADC()
vin = adc.channel(pin='GP3')
lm35 = adc.channel(pin='GP5')

pubCount = 0
nextCount = pubCount

# setup RTC interrupt handler to publish once every period
rtc = machine.RTC()
rtc_i = rtc.irq(trigger=machine.RTC.ALARM0, handler=publish_handler, wake=machine.IDLE)
rtc.alarm(time=60000, repeat=True)

#open client
c = MQTTClient(brdName,"mqtt")
c.connect()
print("connecting to broker")

time.sleep(1)

while True:
    c.publish(brdName+"/iter",str(pubCount))
    c.publish(brdName+"/temp",lm35C_str(lm35))
    c.publish(brdName+"/vin",vin_str(vin))
    nextCount += 1
    while nextCount > pubCount:
        machine.idle()

time.sleep(1)
c.disconnect()