# basic data logger using WiPy
# fork for esp2866 modules
# Niall Parker, 7apr2016
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
    else:
        brdName = 'esp12b'
        adcScl = 531
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
c = MQTTClient(brdName,"mqtt")
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
c.publish(brdName+"/vin",vStr)
time.sleep_ms(100)
c.publish(brdName+"/temp/0",tempStr)

time.sleep(1)
c.disconnect()

print('back to sleep')
machine.deepsleep()     # back to sleep
