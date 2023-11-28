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
from netConfig import RSSI
from boardCfg import mqttHost2
from boardCfg import mqttTopic2
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
sleepTime = minTime*1000
if milliVolts < nomVolts*9/10:
    sleepTime = sleepTime*3
if milliVolts < nomVolts*8/10:
    sleepTime = sleepTime*3
if milliVolts < nomVolts*7/10:
    sleepTime = sleepTime*10 
if milliVolts < nomVolts*6/10:
    sleepTime = sleepTime*10

if sleepTime > 4200000:
    sleepTime = 4200000    # around 70 minutes (max RTC timeout) if very low battery

#optional port for mqttHost
if type(mqttHost) is tuple:
    mqttHost, mqttPort = mqttHost
else:
    mqttPort = 0       # use default

#optional port for mqttHost2
if type(mqttHost2) is tuple:
    mqttHost2, mqttPort2 = mqttHost2
else:
    mqttPort2 = 0       # use default


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
else:
    tempFlg = False

if dhtPin is not None:
    import dht
    ht = dht.DHT22(machine.Pin(dhtPin))
    try:
        ht.measure()
        dhFlag = True
    except:
        dhFlag = False
        print('DHT22 not found')
else:
    dhFlag = False

if sht30Pins is not None:
    try:
        import sht30
        sda, scl = sht30Pins
        sense = sht30.SHT30(scl_pin=scl, sda_pin=sda)
        if not sense.is_present():
            sense = sht30.SHT30(scl_pin=scl, sda_pin=sda, i2c_address=sht30.ALTERNATE_I2C_ADDRESS)
        if sense.is_present():
            sht30Flag = True
        else:
            sht30Flag = False
    except:
        sht30Flag = False
else:
    sht30Flag = False


time.sleep(1)           # allow connection setup and temperature read

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
# for RSSI, from boot.py
message = message + ", 'RSSI' : " + str(RSSI)
message = message + "}"

# add timestamp, NTP sync now in boot.py

message = "{'ts': " + str(time.time()*1000 + 946684800000) + ", 'values': " + message + "}"

import fileQueue
from fileQueue import OK
from fileQueue import NO_MORE_MESSAGES
queue = fileQueue.FILEQUEUE("dataQueue.txt")

if brokerFlg:
    #only do this if we were able to connect to the broker
    publishOK = False
    try:
        c.publish("v1/devices/me/telemetry",message)
        time.sleep(1)
        publishOK = True    # if this message published then don't add to queue
        while 1:
            errorCode, outputMessage = queue.removeFromQueue()
            if( errorCode == OK ):
                c.publish("v1/devices/me/telemetry",outputMessage)
            else:
                break
        c.disconnect()
    except OSError:
        print("Lost broker: msg {}".format(message))
        brokerFlg = False
        if not publishOK:
            print("add msg to queue")
            queue.addToQueue(message)

else:
    print(message)
    print("add msg to queue")
    queue.addToQueue(message)

if mqttHost2 != None:
    try:
        c2 = MQTTClient(brdName,mqttHost2,port=mqttPort2,keepalive=30)
        c2.connect()
        print("connecting to control broker")
        c2.publish(mqttTopic2+"voltage",vStr)
        c2.publish(mqttTopic2+"reset_cause",str(machine.reset_cause()))
        if highPin is not None:
            c2.publish(mqttTopic2+"sw_hi",pin_str(highPin))
        if lowPin is not None:
            c2.publish(mqttTopic2+"sw_lo",pin_str(lowPin))
        if tempFlg:
            c2.publish(mqttTopic2+"temperature",str(ds.read_temp(roms[0])))
        if sht30Flag:
            c2.publish(mqttTopic2+"rh",str(rh))
            c2.publish(mqttTopic2+"temp2",str(t2))
        time.sleep(1)
        c2.disconnect()
    except OSError:
        print("control broker failure")

print('back to sleep: '+ milli_str(sleepTime))
machine.deepsleep(sleepTime)     # back to sleep
