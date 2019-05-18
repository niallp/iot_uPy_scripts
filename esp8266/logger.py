# basic data logger using WiPy
# fork for esp2866 modules
# Niall Parker, 7apr2016
# adapt for Thingsboard demo
# isolate board specific values to boardCfg.py

import socket
import time
import machine
import os

from umqtt_simple import MQTTClient

import onewire
import ds18x20
import dht

from boardCfg import brdName
from boardCfg import adcScl
from boardCfg import userToken
from boardCfg import mqttHost

# account for voltage divider of 100k over 22k on Vinput: tweaked to calibrate
def vin_str(adc,scl):
    acc = 0
    for r in range(10):     # average over 10 in case of noise
        acc += adc()
    milliVolts = ((acc-25)*scl) // 1024
    return str(milliVolts // 1000) + "." + "{0:0>3}".format(milliVolts % 1000) 

#setup 
adc = machine.ADC(0)
vin = adc.read
# configure wakeup
rtc = machine.RTC()
rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
rtc.alarm(rtc.ALARM0,60000)

#open client
c = MQTTClient(brdName,mqttHost,keepalive=30,user=userToken,password='')
# extra delay to allow network to stabilize
time.sleep(1)           
c.connect()
print("connecting to broker")

ds = ds18x20.DS18X20(onewire.OneWire(machine.Pin(12)))
roms = ds.scan()
if len(roms) == 0:
    tempFlg = False
else:
    ds.convert_temp()
    tempFlg = True

ht = dht.DHT22(machine.Pin(13))
try:
    ht.measure()
    dhFlag = True
except:
    dhFlag = False

time.sleep(1)           # allow connection setup and temperature read
if tempFlg:
    tempStr = str(ds.read_temp(roms[0]))
else:
    tempStr = "none"
vStr = vin_str(vin,adcScl)
if dhFlag:
    c.publish("v1/devices/me/telemetry","{'volts' : "+vStr+ ", 'temperature' : "+ tempStr + ", 'temp2' : "+ str(ht.temperature()) + ", 'rh1' : "+ str(ht.humidity()) +"}")
else:
    c.publish("v1/devices/me/telemetry","{'volts' : "+vStr+ ", 'temperature' : "+ tempStr + "}")
time.sleep_ms(100)

time.sleep(1)
c.disconnect()

print('back to sleep')
machine.deepsleep()     # back to sleep
