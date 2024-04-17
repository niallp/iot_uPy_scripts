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
from boardCfg import mqttTopic2
from boardCfg import highPin
from boardCfg import lowPin
from boardCfg import oneWirePin
from boardCfg import dhtPin
from boardCfg import sht30Pins
from netConfig import RSSI
 
# now uses calibrated function on ESP32 instead of manual scaling
def vin_mV(adc,scl):
    acc = 0
    for r in range(10):     # average over 10 in case of noise
        acc += adc.read_uv()
    print("ADC: ", acc/10)
    milliVolts = ((acc/10)*2/1000)
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
    brokerFlg = True
    print("brokerFLg = True")

except:
    print("brokerFLg = False")
    brokerFlg = False

if oneWirePin is not None:
    import onewire
    import ds18x20
    ds = ds18x20.DS18X20(onewire.OneWire(machine.Pin(oneWirePin)))
    roms = ds.scan()
    if len(roms) == 0:
        tempFlg = False
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

if sht30Flag:
    try:
        t2, rh = sense.measure()
    except:
        sht30Flag = False
    
message = "{ "
message = message + "'volts' : " + str(milliVolts/1000)
message = message + ", 'RSSI' : " + str(netConfig.RSSI)
if sht30Flag:
    message = message + ", 'temp2': "+ str(t2)
    message = message + ", 'humidity': "+ str(rh)
if tempFlg:
    message = message + ", 'temperature' : " + str(ds.read_temp(roms[0]))
message = message + " }"
    
import fileQueue
from fileQueue import OK
from fileQueue import NO_MORE_MESSAGES
queue = fileQueue.FILEQUEUE("dataQueue.txt")


if brokerFlg:
    #sync to NTP time
    #only do this if we were able to connect to the broker
    import ntptime
    ntptime.host = "0.ca.pool.ntp.org"

    try:
        ntptime.settime()
        print("ntptime worked")
        
    except:
        print("ntptime error: ")
        
    #add timestamp here for best value of time
    message = "{'ts': " + str(time.time()*1000 + 946684800000) + ", 'values': " + message + " }"
    print("Sending message: " + message)
    
    try:
        c.publish("v1/devices/me/telemetry",message)
        time.sleep(1)
        while 1 :
            errorCode, outputMessage = queue.removeFromQueue()
            if( errorCode == OK ):
                c.publish("v1/devices/me/telemetry",outputMessage)
            else:
                break
        c.disconnect()

    except:
        print("Failed to publish: ", message)
        queue.addToQueue(message)

else:
    # timestamp may not be great but best we can do without NTP
    message = "{'ts': " + str(time.time()*1000 + 946684800000) + ", 'values': " + message + " }"
    queue.addToQueue(message)
    print("Adding to queue: " + message )

    
machine.deepsleep(10000)


