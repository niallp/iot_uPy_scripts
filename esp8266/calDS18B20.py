# util for display of DS18B20 data

import socket
import time
import machine
import os

from umqtt_simple import MQTTClient


from boardCfg import brdName
from boardCfg import adcScl
from boardCfg import userToken
from netConfig import mqttHost
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

def scanDS18B20(oneWirePin):
    global ds
    if oneWirePin is not None:
        import onewire
        import ds18x20
        ds = ds18x20.DS18X20(onewire.OneWire(machine.Pin(oneWirePin)))
        roms = ds.scan()
        if len(roms) == 0:
            print('DS18x20 not found')
            return False
        else:
            ds.convert_temp()
            return roms
    else:
        return False

def dispDS18B20(roms):
    if len(roms) > 0:
        message = "{"
        message += "'temp{}' : {}".format(0,readDS(roms[0]))
        for ti in range(1,len(roms)):
            message += ", 'temp{}' : {}".format(ti,readDS(roms[ti]))
        message += "}"
        return message
    else:
        return ''

def dispAvgOff(roms,n,offset):
    global ds
    accum = [0.0] * len(roms)
    for i in range(n):
        ds.convert_temp()
        time.sleep(1)
        for ti in range(len(roms)):
            accum[ti] += readDS(roms[ti])
    print(''.join('{} '.format(accum[x]/n-offset) for x in range(len(roms))))

def dispAvg(roms,n):
    dispAvgOff(roms,n,0.0)

#optional port for mqttHost
if type(mqttHost) is tuple:
    mqttHost, mqttPort = mqttHost
else:
    mqttPort = 0       # use default


roms = scanDS18B20(oneWirePin)
hdr = ''
for r in roms:
    hdr += ''.join('{:02x}'.format(x) for x in r)
    hdr += ' '
print(hdr)
dispAvg(roms,10)

#open client
try:
    c = MQTTClient(brdName,mqttHost,port=mqttPort,keepalive=30,user=userToken,password='')
    # extra delay to allow network to stabilize
    time.sleep(1)           
    c.connect()
    print("connecting to broker")
    brokerFlg = True
except:
    print("failure to connect to broker")
    brokerFlg = False

for i in range(10000):
    msg = dispDS18B20(roms)
    ds.convert_temp()
    print('{}:{}'.format(i,msg))
    if brokerFlg:
        c.publish("v1/devices/me/telemetry",msg)
    time.sleep(10)

c.disconnect()

