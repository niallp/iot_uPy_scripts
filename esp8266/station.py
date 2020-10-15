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

from boardCfg import brdName
from boardCfg import adcScl
from boardCfg import userToken
from netConfig import mqttHost
from boardCfg import mqttHost2

import sht30

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

sense1 = sht30.SHT30()
sense2 = sht30.SHT30(i2c_address=sht30.ALTERNATE_I2C_ADDRESS)

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


time.sleep(1)           # allow connection setup and temperature read
vStr = vin_str(vin,adcScl)
message = "{'volts' : "+vStr
if sense1.is_present():
    t1,rh1 = sense1.measure()
    message = message + ", 'temperature' : " + str(t1) + ", 'rh1' : " + str(rh1)
if sense2.is_present():
    t2,rh2 = sense2.measure()
    message = message + ", 'temp2' : " + str(t2) + ", 'rh2' : " + str(rh2)
message = message + "}"

if brokerFlg:
    c.publish("v1/devices/me/telemetry",message)
    time.sleep(1)
    c.disconnect()


print('back to sleep')
machine.deepsleep()     # back to sleep
