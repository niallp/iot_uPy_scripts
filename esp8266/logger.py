# basic data logger using WiPy
# fork for esp2866 modules
# Niall Parker, 7apr2016
# adapt for Thingsboard demo

import socket
import time
import machine
import os

from umqtt_simple import MQTTClient

import onewire
import ds18x20

mch = os.uname().machine
uniq = machine.unique_id()
if 'ESP8266' in mch:
    if uniq[0] == 0x5d:
        brdName = 'esp12a'
        adcScl = 548
        userToken = 'AAcN0MpuEnze9URXyBJ9'
    elif uniq == b'\x02\t\xf9\x00':
        brdName = 'esp12b'
        adcScl = 531
        userToken = 'R3piEqJNiAxassZHL84O'
    elif uniq == b'\x99\xf1\xf3\x00':
        brdName = 'esp12c'
        adcScl = 540
        userToken = 'lLCGCMDBHl3G7FUHJ6LR'
    else:
        brdName = 'esp12d'
        adcScl = 540
        userToken = 'eubEzHnrUFsFOaT9uNjS'
else:
    print("Board not recognized, for ESP2866 only now")
    raise SystemExit

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
c = MQTTClient(brdName,"thingsboard",keepalive=30,user=userToken,password='')
# extra delay to allow network to stabilize
time.sleep(1)           
c.connect()
print("connecting to broker")

ow = machine.Pin(12)
ds = ds18x20.DS18X20(onewire.OneWire(ow))
roms = ds.scan()
if len(roms) == 0:
    tempFlg = False
else:
    ds.convert_temp()
    tempFlg = True

time.sleep(1)           # allow connection setup and temperature read
if tempFlg:
    tempStr = str(ds.read_temp(roms[0]))
else:
    tempStr = "none"
vStr = vin_str(vin,adcScl)
c.publish("v1/devices/me/telemetry","{'volts' : "+vStr+ ", 'temperature' : "+ tempStr + "}")
time.sleep_ms(100)

time.sleep(1)
c.disconnect()

print('back to sleep')
machine.deepsleep()     # back to sleep
