# datalogger and station controller, Niall Parker 10nov2020

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
from boardCfg import minTime
from boardCfg import nomVolts
from ds18B20cal import offsets

# account for voltage divider of 100k over 22k on Vinput: tweaked to calibrate
def vin_mV(adc,scl):
    acc = 0
    for r in range(10):     # average over 10 in case of noise
        acc += adc()
    milliVolts = ((acc-30)*scl) // 1024
    return milliVolts

def milli_str(millis):
    return str(millis // 1000) + "." + "{0:0>3}".format(millis % 1000) 

def pin_str(gpio):
    # default switches pulled high so active low
    pin = machine.Pin(gpio,machine.Pin.IN,machine.Pin.PULL_UP)
    return '1' if pin.value() == 0 else '0'

def relayCtl(topic, msg):
    global relay, acOn
    print("Topic: "+str(topic.decode())+" Msg: "+str(msg.decode()))
    if topic.endswith('inverter'):
        acOn = bool(int(msg))
    if topic.endswith('relay'):
        relay.value(int(msg))

def readDS(addr):
    global offsets
    if bytes(addr) in offsets:
        return ds.read_temp(addr) - offsets[bytes(addr)]
    else:
        return ds.read_temp(addr)

def blip(relay):
    relay.value(1)
    time.sleep_ms(200)
    relay.value(0)
    time.sleep_ms(50)

#setup 
adc = machine.ADC(0)
milliVolts = vin_mV(adc.read,adcScl)    # want to sleep longer if voltage is low
sleepTime = minTime*1000                # (ms)
if mqttHost2 != None and mqttTopic2 != None:
    ctlFlg = True
else:
    ctlFlg = False
if milliVolts < nomVolts*9/10:
    sleepTime = sleepTime*3
if milliVolts < nomVolts*8/10:
    sleepTime = sleepTime*3
if milliVolts < nomVolts*7/10:
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

# configure sensors
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
    import sht30
    sda, scl = sht30Pins
    sense1 = sht30.SHT30(scl_pin=scl, sda_pin=sda)
    sense2 = sht30.SHT30(scl_pin=scl, sda_pin=sda, i2c_address=sht30.ALTERNATE_I2C_ADDRESS)  
    sht30Flag = sense1.is_present() | (sense2.is_present() << 1)
    if not sht30Flag:
        print('SHT30 sensor(s) not found')
else:
    sht30Flag = False

relay = machine.Pin(15,machine.Pin.OUT)
relay.value(0)
acPresentPin = machine.Pin(13,machine.Pin.IN,machine.Pin.PULL_UP)
acPresent = not bool(acPresentPin.value())
acOn = acPresent        # first time we accept existing state of power

while ctlFlg:
    if milliVolts < nomVolts/2:  #ie station battery low
        print("low battery, monitor only")
        ctlFlg = False
        sleepTime = 120000

    #open client
    try:
        cTb = MQTTClient(brdName,mqttHost,port=mqttPort,keepalive=30,user=userToken,password='')
        # extra delay to allow network to stabilize
        time.sleep_ms(100)           
        cTb.connect()
        print("connecting to broker")
        brokerFlg = True
    except:
        print("failure to connect to broker")
        brokerFlg = False

    #for controller
    if ctlFlg:
        try:
            cCtl = MQTTClient(brdName,mqttHost2,port=mqttPort2,keepalive=60)
            cCtl.set_callback(relayCtl)
            cCtl.connect()
            print("connecting to controller")
            if type(mqttTopic2) is list:
                for t in mqttTopic2:
                    cCtl.subscribe(t)
            else:
                cCtl.subscribe(mqttTopic2)
        except:
            print("failure to connect to controller")
            ctlFlg = False


    time.sleep_ms(100)           # allow connection setup and temperature read
    message = "{"
    milliVolts = vin_mV(adc.read,adcScl)
    vStr = milli_str(milliVolts)
    message += "'volts' : {}".format(vStr)
    if tempFlg:
        message += ", 'temperature' : {}".format(readDS(roms[0]))
        if len(roms) > 1:
            for ti in range(1,len(roms)):
                message += ", 'temp{}' : {}".format(ti+2,readDS(roms[ti]))
    if sht30Flag:
        if sense1.is_present():
            t1,rh1 = sense1.measure()
            message += ", 'temp1' : {}, 'rh1' : {}".format(t1,rh1)
        if sense2.is_present():
            t2,rh2 = sense2.measure()
            message += ", 'temp2' : {}, 'rh2' : {}".format(t2,rh2)
    if ctlFlg:
        message += ", 'acOn' : {}".format(acOn)
        message += ", 'acPresent' : {}".format(acPresent)
    message += "}"

    if brokerFlg:
        try:
            cTb.publish("v1/devices/me/telemetry",message)
            time.sleep_ms(100)
            cTb.disconnect()
        except:
            print("Lost broker: msg {}".format(message))
    else:
        print(message)


    if not ctlFlg:
        print('back to sleep: '+milli_str(sleepTime))
        relay.value(0)
        machine.deepsleep(sleepTime)     # back to sleep
    else:
        print('awake but waiting: '+milli_str(sleepTime))
        if tempFlg:
            ds.convert_temp()
        start = time.ticks_ms()
        while (time.ticks_diff(time.ticks_ms(),start) < sleepTime) and ctlFlg:
            acPresent = not bool(acPresentPin.value())
            try:
                oldAC = acOn
                cCtl.check_msg()
            except:
                ctlFlg = False
            if oldAC != acOn:
                if acOn and not acPresent:
                    blip(relay)
                if not acOn and acPresent:
                    blip(relay)
            time.sleep_ms(100)          # idle and let inverter settle

print("Lost control broker, restarting")
time.sleep(60)
machine.reset()
