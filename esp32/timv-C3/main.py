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

'''
from __init__ import Logger
from __init__ import CRITICAL
from __init__ import ERROR
from __init__ import WARNING
from __init__ import INFO
from __init__ import DEBUG
from __init__ import NOTSET
global logger
'''

from boardCfg import brdName
from boardCfg import adcScl
from boardCfg import userToken
from netConfig import mqttHost
from boardCfg import mqttHost2
from boardCfg import mqttTopic2
from boardCfg import highPin
from boardCfg import lowPin
from boardCfg import oneWirePin
from boardCfg import dhtPin
from boardCfg import sht30Pins
 
# account for voltage divider of 100k over 22k on Vinput: tweaked to calibrate
def vin_mV(adc,scl):
    acc = 0
    for r in range(10):     # average over 10 in case of noise
#        val = adc.read_uv()
#        print("adc: ", val)
        acc += adc.read_uv()
    print("ADC: ", acc/10)
   # milliVolts = ((acc-25)*scl) // 1024
    milliVolts = ((acc/10)*2/1000)
    #logger.info("milliVolts: " + str(milliVolts))
    return milliVolts

def vin_str(milliVolts):
    return str(milliVolts // 1000) + "." + "{0:0>3}".format(milliVolts % 1000) 

def pin_str(gpio):
    # default switches pulled high so active low
    pin = machine.Pin(gpio,machine.Pin.IN,machine.Pin.PULL_UP)
    return '1' if pin.value() == 0 else '0'

from machine import ADC, Pin
adc = ADC(Pin(3))
adc.atten(ADC.ATTN_11DB)
#print("16bit Val: ", adc.read_u16())
#print("uv Val: ", adc.read_uv())
milliVolts = vin_mV(adc,adcScl)    # want to sleep longer if voltage is low
print("milliVolts: ", milliVolts)
'''
sleepTime = 60000
if milliVolts < 3700:
    sleepTime = sleepTime*10
if milliVolts < 3400:
    sleepTime = sleepTime*3
if milliVolts < 3200:
    sleepTime = sleepTime*4     # around 2 hours if very low battery
'''

#optional port for mqttHost
if type(mqttHost) is tuple:
    mqttHost, mqttPort = mqttHost
else:
    mqttPort = 0       # use default

#open client if wifi connected
import netConfig
from netConfig import wifiConnected
print("main: wificonnected: ", netConfig.wifiConnected)
try:
    c = MQTTClient(brdName,mqttHost,keepalive=300,user=userToken,password='')
    # extra delay to allow network to stabilize
    time.sleep(1)
    c.connect()
    #logger.info("connecting to broker")
    brokerFlg = True
    print("brokerFLg = True")

except:
    #logger.error("failure to connect to broker")
    print("brokerFLg = False")
    brokerFlg = False

if oneWirePin is not None:
    import onewire
    import ds18x20
    ds = ds18x20.DS18X20(onewire.OneWire(machine.Pin(oneWirePin)))
    roms = ds.scan()
    if len(roms) == 0:
        tempFlg = False
        #logger.info('DS18x20 not found')
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
        #logger.warning('DHT22 not found')
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

'''
vStr = vin_str(milliVolts)
#message = "{'volts' : "+vStr
message ="{'volts' : " + str(milliVolts/1000)
if highPin is not None:
    message = message + ", 'sw_high' : "+pin_str(highPin)
if lowPin is not None:
    message = message + ", 'sw_low' : "+pin_str(lowPin)
if tempFlg:
    message = message + ", 'temperature' : " + str(ds.read_temp(roms[0]))
# only expect one of following RH sensors installed
if dhFlag:
    message = message + ", 'temp2' : "+ str(ht.temperature()) + ", 'rh1' : "+ str(ht.humidity())
if sht30Flag:
    t2, rh = sense.measure()
    message = message + ", 'temp2' : "+ str(t2) + ", 'rh1' : "+ str(rh)
    
message = message + "}"
'''
if sht30Flag:
    try:
        t2, rh = sense.measure()
    except:
        t2=0
        rh=0  
else:
    t2=0
    rh=0
    
    
    #message2 = "{'ts': 1527863043000, 'temperature': 42.2, 'humidity': 70  }"
    
#logger.critical("log message2:" + message2)

#logger.critical("log message:" + message)
import fileQueue
from fileQueue import OK
from fileQueue import NO_MORE_MESSAGES
queue = fileQueue.FILEQUEUE("dataQueue.txt")



if brokerFlg:
    #logger.info("about to publish")
    #sync to NTP time
    #only do this if we were able to connect to the broker
    import ntptime
    ntptime.host = "0.ca.pool.ntp.org"

    try:
        ntptime.settime()
        print("ntptime worked")
        
    except:
        print("ntptime error: ")
        
    import netConfig
    from netConfig import RSSI
 
    message = "{'ts': " + str(time.time()*1000 + 946684800000)
    message = message + ", 'values': { 'temperature': "+ str(t2)
    message = message + ", 'humidity': "+ str(rh)
    message = message + ", 'volts' : " + str(milliVolts/1000)
    message = message + ", 'RSSI' : " + str(netConfig.RSSI)
    message = message + " } }"
    print("Sending message: " + message)
    
    try:
        c.publish("v1/devices/me/telemetry",message)
        time.sleep(1)
        while 1 :
            errorCode, outputMessage = queue.removeFromQueue()
            #print("errorCode, outputMessage: ", str(errorCode), outputMessage)
            if( errorCode == OK ):
                c.publish("v1/devices/me/telemetry",outputMessage)
                #print(" removing from Queue: ", outputMessage)
                #time.sleep(1)
            else:
                break
        c.disconnect()

    except:
        print("Failed to publish: ", message)
        queue.addToQueue(message)
        

else:

    message = "{'ts': " + str(time.time()*1000 + 946684800000)
    message = message + ", 'values': { 'temperature': "+ str(t2)
    message = message + ", 'humidity': "+ str(rh)
    message = message + ", 'volts' : " + str(milliVolts/1000)
    cmessage = message + ", 'RSSI' : " + str(netConfig.RSSI)
    message = message + " } }"
    queue.addToQueue(message)
    print("Adding to queue: " + message )

    
#logger.info('back to sleep: 60000 ')
#machine.deepsleep(4200000)     # back to sleep
#time.sleep(5)
#print('deepsleep 2 hours')
#time.sleep(120)
# machine.deepsleep(7200000)
machine.deepsleep(10000)


