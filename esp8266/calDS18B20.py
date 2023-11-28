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
from netConfig import RSSI
from boardCfg import highPin
from boardCfg import lowPin
from boardCfg import oneWirePin
from boardCfg import dhtPin
from boardCfg import sht30Pins
from boardCfg import minTime
from boardCfg import nomVolts
from ds18B20cal import offsets

# account for voltage divider of 100k over 22k on Vinput: tweaked to calibrate
def vin_mV(adc,scl):
    acc = 0
    for r in range(10):     # average over 10 in case of noise
        acc += adc()
    milliVolts = ((acc-25)*scl) // 1024
    return milliVolts

def milli_str(millis):
    return str(millis // 1000) + "." + "{0:0>3}".format(millis % 1000) 

def pin_str(gpio):
    # default switches pulled high so active low
    pin = machine.Pin(gpio,machine.Pin.IN,machine.Pin.PULL_UP)
    return '1' if pin.value() == 0 else '0'

def readDS(addr):
    global offsets
    if bytes(addr) in offsets:
        return ds.read_temp(addr) - offsets[bytes(addr)]
    else:
        return ds.read_temp(addr)

#setup 
adc = machine.ADC(0)
milliVolts = vin_mV(adc.read,adcScl)    # want to sleep longer if voltage is low
sleepTime = 10000

brokerFlg = False

if oneWirePin is not None:
    import onewire
    import ds18x20
    ds = ds18x20.DS18X20(onewire.OneWire(machine.Pin(oneWirePin)))
    roms = ds.scan()
    if len(roms) == 0:
        tempFlg = False
        print('DS18x20 not found')
    else:
        ds.convert_temp()
        tempFlg = True
        print(roms)
else:
    tempFlg = False

dhFlag = False
sht30Flag = False

for t in range(1000):
    time.sleep(1)           # allow temperature read

    vStr = milli_str(milliVolts)
    message = "{'volts' : "+vStr
    if highPin is not None:
        message = message + ", 'sw_high' : "+pin_str(highPin)
    if lowPin is not None:
        message = message + ", 'sw_low' : "+pin_str(lowPin)
    if tempFlg:
        message += ", 'temperature' : {}".format(readDS(roms[0]))
        # any additional 1W sensors will carry on at temp3 etc.
        if len(roms) > 1:
                for ti in range(1,len(roms)):
                    message += ", 'temp{}' : {}".format(ti+2,readDS(roms[ti]))
    # only expect one of following RH sensors installed
    if dhFlag:
        message = message + ", 'temp2' : "+ str(ht.temperature()) + ", 'rh1' : "+ str(ht.humidity()) 
    if sht30Flag:
        t2, rh = sense.measure()
        message = message + ", 'temp2' : "+ str(t2) + ", 'rh1' : "+ str(rh) 
    message = message + "}"

    if not brokerFlg:
        print(message)

    print('back to sleep: '+ milli_str(sleepTime))
    time.sleep_ms(sleepTime)
