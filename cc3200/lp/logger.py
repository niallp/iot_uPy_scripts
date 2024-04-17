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

if machine.unique_id() == b'TJ\x16.\xdb\xfe':
    brdName = 'lp2'
    userToken = 'qwA3HRsc2WNu4Fi0Qmpy'
else:
    brdName = 'lp1'
    userToken = 'taar3KNm6nR6Bu9iThXV'  # for thingsboard


TMP006_ADDR = 65                    # TMP006 on default I2C bus, just using die temperature for now

# count ticks
def tick_handler(rtc_o):
    global ticks
    ticks += 1
    if ticks == 30:
        ticks = 0
        publish_handler(None)

# for periodic publishing
def publish_handler(pin):
    global pubCount
    p_red.value(1)
    pubCount += 1
    p_red.value(0)

# to remotely stop logger
def checkStop_cb(topic,msg):
    global loggerStop
    if int(msg):
        loggerStop = True

# returns temperature in degree C from AD592 as string
def ad592_str(adc):
    milliVolts = (adc()*1494) // 4096
    tempK10 = (milliVolts*10000) // 4460      # Kelvin*10, 4k46 Rsense
    tempC10 = tempK10 - 2732
    return str(tempC10 // 10) + "." + str(tempC10 % 10)

def dieTemp_str(i2c,addr):
    dTemp = struct.unpack(">h",i2c.readfrom_mem(addr,1,2))[0]
    return str(dTemp // 128) + "." + str((dTemp % 128)*100 // 128)

# account for voltage divider, 100k over [3k3, 4k7, 10k]
# calibrated against MS8209 DVM, np 16may2020
def volt_str(ch,scale):
    adc = machine.ADC().channel(ch)
    acc = 0
    for i in range(16):
        acc += adc()
    milliVolts = (acc*scale) >> (12+4)
    return str(milliVolts // 1000) + "." + str(milliVolts % 1000)

def sw_str(switch):
    return str(switch.value())

#setup 
wipy.heartbeat(False)
loggerStop = False
ticks = 0
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

sw_hi = Pin('GP13', mode=Pin.IN, pull=None)  # left hand (SW3), note external pulldown
sw_lo = Pin('GP22', mode=Pin.IN, pull=None)  # right hand (SW2)

# single point calibration against MS8209 DVM, 18dec2022
adc = { 'vB24' : (1,33212), 'vB12' : (2,17061), 'vSolar' : (3,45139) }

pubCount = 0
nextCount = pubCount

# setup RTC interrupt handler to publish once every period
rtc = machine.RTC()
rtc_i = rtc.irq(trigger=machine.RTC.ALARM0, handler=tick_handler, wake=machine.SLEEP)
rtc.alarm(time=1000, repeat=True)

# allow wakeup with switch inputs as well (faster response)
# note only last enabled interrupt active for machine.SLEEP
# need to go to DEEPSLEEP and restart to permit multiple pins
sw_hi.irq(handler=publish_handler, trigger=Pin.IRQ_RISING, wake=machine.SLEEP)

#open client for local access (controller, node-red)
c = MQTTClient(brdName,"mqtt",keepalive=60)
c.set_callback(checkStop_cb)
#open 2nd connection for datalogging in thingsboard
tb = MQTTClient(brdName,'thingsboard.balsk.ca',keepalive=30,user=userToken,password='')
utime.sleep(1)

controlFlg = False

try:
    c.connect()
    c.subscribe(brdName+"/loggerStop")
    print("connected to mqtt")
    controlFlg = True
except:
    print("error connecting to mqtt, no control")



while not loggerStop:
    try:
        tb_msg = "{"
        if controlFlg:
            c.publish(brdName+"/iter",str(pubCount))
        else:
            print("Iter: {}",str(pubCount))
        for topic,chScl in adc.items():
            mVolts = volt_str(chScl[0],chScl[1])
            tb_msg += "'{}' : {},".format(topic,mVolts)
            if controlFlg:
                c.publish(brdName+"/"+topic,mVolts)
        if tempFlg:
            tempStr = dieTemp_str(i2c,TMP006_ADDR)
            tb_msg += "'temperature' : {},".format(tempStr)
            if controlFlg:
                c.publish(brdName+"/temperature",tempStr)
        if controlFlg:
            c.publish(brdName+"/sw_high",sw_str(sw_hi))
            c.publish(brdName+"/sw_low",sw_str(sw_lo))
        tb_msg += "'sw_high' : {}, 'sw_low' : {} }}".format(sw_str(sw_hi),sw_str(sw_lo))
        tb.connect()
        print("connected to thingsboard")
        tb.publish("v1/devices/me/telemetry",tb_msg)
        nextCount += 1
        tb.disconnect()
        while nextCount > pubCount and not loggerStop:
            if controlFlg:
                c.check_msg()
            machine.lightsleep()    # now RTC on 1 Hz tick
    except:
        print("error publishing to tb, should queue data")
        utime.sleep(3)
#        machine.reset()

c.disconnect()

print("Exited logger")
