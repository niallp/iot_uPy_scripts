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
from netConfig import mqttHost
from boardCfg import mqttHost2
from boardCfg import mqttTopic2

# account for voltage divider of 100k over 22k on Vinput: tweaked to calibrate
def vin_mV(adc,scl):
    acc = 0
    for r in range(10):     # average over 10 in case of noise
        acc += adc()
    milliVolts = ((acc-25)*scl) // 1024
    return milliVolts

def vin_str(milliVolts):
    return str(milliVolts // 1000) + "." + "{0:0>3}".format(milliVolts % 1000) 

#setup 
adc = machine.ADC(0)
milliVolts = vin_mV(adc.read,adcScl)    # want to sleep longer if voltage is low
sleepTime = 60000
if milliVolts < 3700:
    sleepTime = sleepTime*10
if milliVolts < 3400:
    sleepTime = sleepTime*3
if milliVolts < 3200:
    sleepTime = sleepTime*4     # around 2 hours if very low battery

# configure wakeup
rtc = machine.RTC()
rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
rtc.alarm(rtc.ALARM0,sleepTime)

#open client
try:
    c = MQTTClient(brdName,mqttHost,keepalive=30,user=userToken,password='')
    # extra delay to allow network to stabilize
    time.sleep(1)           
    c.connect()
    print("connecting to broker")
    brokerFlg = True
except OSError:
    print("failure to connect to broker")
    brokerFlg = False



lvlFlg = True
if lvlFlg:
    # level switches on pins 4,5
    p_hi = machine.Pin(4,machine.Pin.IN,machine.Pin.PULL_UP)
    p_lo = machine.Pin(5,machine.Pin.IN,machine.Pin.PULL_UP)

    if p_hi.value() == 0:
        sw_high = '1'
    else:
        sw_high = '0'

    if p_lo.value() == 0:
        sw_low = '1'
    else:
        sw_low = '0'


ds = ds18x20.DS18X20(onewire.OneWire(machine.Pin(12)))
roms = ds.scan()
if len(roms) == 0:
    tempFlg = False
    print('DS18x20 not found')
else:
    ds.convert_temp()
    tempFlg = True

ht = dht.DHT22(machine.Pin(13))
try:
    ht.measure()
    dhFlag = True
except:
    dhFlag = False
    print('DHT22 not found')

time.sleep(1)           # allow connection setup and temperature read

vStr = vin_str(milliVolts)
message = "{'volts' : "+vStr
if lvlFlg:
    message = message + ", 'sw_high' : "+sw_high+", 'sw_low' : "+sw_low
if tempFlg:
    message = message + ", 'temperature' : " + str(ds.read_temp(roms[0]))
if dhFlag:
    message = message + ", 'temp2' : "+ str(ht.temperature()) + ", 'rh1' : "+ str(ht.humidity()) 
message = message + "}"

if brokerFlg:
    c.publish("v1/devices/me/telemetry",message)

    time.sleep(1)
    c.disconnect()

if mqttHost2 != None:
    try:
        c2 = MQTTClient(brdName,mqttHost2,keepalive=30)
        c2.connect()
        print("connecting to control broker")
        c2.publish(mqttTopic2+"voltage",vStr)
        if lvlFlg:
            c2.publish(mqttTopic2+"sw_hi",sw_high)
            c2.publish(mqttTopic2+"sw_lo",sw_low)
        time.sleep(1)
        c2.disconnect()
    except OSError:
        print("control broker failure")

print('back to sleep: '+ str(sleepTime))
machine.deepsleep()     # back to sleep

