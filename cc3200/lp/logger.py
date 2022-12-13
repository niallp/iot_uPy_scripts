# basic data logger using WiPy
# fork back to wipy, now mods for LAUNCHXL
# Niall Parker, 7apr2016, 12dec2022
from machine import Pin
import socket
import utime
import machine
import struct
import os
import wipy

from umqtt_simple import MQTTClient

brdName = 'lp1'
userToken = 'taar3KNm6nR6Bu9iThXV'  # for thingsboard
TMP006_ADDR = 65                    # TMP006 on default I2C bus, just using die temperature for now

# for periodic publishing
def publish_handler(rtc_o):
    global pubCount
    p_red.value(1)
    pubCount += 1
    p_red.value(0)

# returns temperature in degree C from AD592 as string
def ad592_str(adc):
    milliVolts = (adc()*1494) // 4096
    tempK10 = (milliVolts*10000) // 4460      # Kelvin*10, 4k46 Rsense
    tempC10 = tempK10 - 2732
    return str(tempC10 // 10) + "." + str(tempC10 % 10)

def dieTemp_str(i2c,addr):
    dTemp = struct.unpack(">h",i2c.readfrom_mem(addr,1,2))[0]
    return str(dTemp // 128) + "." + str((dTemp % 128)*100 // 128)

# account for voltage divider of 115k over 56k on Vbatt (on expansion board)
# calibrated against MS8209 DVM, np 16may2020
def vbatt_str(adc):
    milliVolts = (adc()*4722) // 4096
    return str(milliVolts // 1000) + "." + str(milliVolts % 1000)

def sw_str(switch):
    return str(switch.value())

#setup 
wipy.heartbeat(False)
p_red = Pin('GP9', mode=Pin.OUT)       # used for system (heartbeat) by default
p_red.value(0)
# green and yellow LEDs conflict with I2C default pins
#p_grn = Pin('GP11', mode=Pin.OUT)
#p_grn.value(0)
#p_yel = Pin('GP10', mode=Pin.OUT)
#p_yel.value(0)		# turn off LED

tempFlg = False
i2c = machine.I2C(0,scl='GP10',sda='GP11',freq=400000)
if TMP006_ADDR in i2c.scan():
    if i2c.readfrom_mem(TMP006_ADDR,254,2) == b'TI' and i2c.readfrom_mem(TMP006_ADDR,255,2) == b'\x00g':
        tempFlg = True

sw_hi = Pin('GP13', mode=Pin.IN, pull=Pin.PULL_UP)
sw_lo = Pin('GP22', mode=Pin.IN, pull=Pin.PULL_UP)

adc = machine.ADC()
vbatt24 = adc.channel(1)
vbatt12 = adc.channel(2)
vSolar = adc.channel(3)

pubCount = 0
nextCount = pubCount

# setup RTC interrupt handler to publish once every period
rtc = machine.RTC()
rtc_i = rtc.irq(trigger=machine.RTC.ALARM0, handler=publish_handler, wake=machine.SLEEP)
rtc.alarm(time=30000, repeat=True)

# allow wakeup with switch inputs as well (faster response)
# note only last enabled interrupt active for machine.SLEEP
# need to go to DEEPSLEEP and restart to permit multiple pins
sw_hi.irq(handler=publish_handler, trigger=Pin.IRQ_RISING, wake=machine.SLEEP)

#open client for local access (controller, node-red)
c = MQTTClient(brdName,"mqtt")
#open 2nd connection for datalogging in thingsboard
tb = MQTTClient(brdName,'thingsboard.balsk.ca',keepalive=30,user=userToken,password='')
utime.sleep(1)

while True:
    try:
        c.connect()
        print("connecting to mqtt")
        tb.connect()
        print("connecting to thingsboard")
        tb_msg = "{"
        c.publish(brdName+"/iter",str(pubCount))
        vSol_str = str(vSolar())
        c.publish(brdName+"/vSolar",vSol_str)
        tb_msg += "'vSolar' : {},".format(vSol_str)
        if tempFlg:
            tempStr = dieTemp_str(i2c,TMP006_ADDR)
            tb_msg += "'temperature' : {},".format(tempStr)
            c.publish(brdName+"/temperature",tempStr)
        vB24_str =str(vbatt24())
        c.publish(brdName+"/vB24",vB24_str)
        tb_msg += "'vB24' : {},".format(vB24_str)
        vB12_str =str(vbatt12())
        c.publish(brdName+"/vB12",vB12_str)
        tb_msg += "'vB12' : {},".format(vB12_str)
        c.publish(brdName+"/sw_high",sw_str(sw_hi))
        c.publish(brdName+"/sw_low",sw_str(sw_lo))
        tb_msg += "'sw_high' : {}, 'sw_low' : {} }}".format(sw_str(sw_hi),sw_str(sw_lo))
        tb.publish("v1/devices/me/telemetry",tb_msg)
        nextCount += 1
        c.disconnect()
        tb.disconnect()
    except OSError:
        utime.sleep(30)
        machine.reset()
    while nextCount > pubCount:
        machine.lightsleep()

print("Exited logger")
