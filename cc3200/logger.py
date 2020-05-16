# basic data logger using WiPy
# fork back to wipy
# Niall Parker, 7apr2016
from machine import Pin
import socket
import utime
import machine
import os
import wipy

from umqtt_simple import MQTTClient

mch = os.uname().machine
uniq = machine.unique_id()
if 'WiPy' in mch:
    brdName = 'wipy'
else:
    print("wipy only now")
    raise SystemExit

# for periodic publishing
def publish_handler(rtc_o):
    global pubCount
    p_usr.value(0)
    pubCount += 1
    p_usr.value(1)

# returns temperature in degree C from AD592 as string
def ad592_str(adc):
    tempK10 = (adc()*11000000*4) // (3 * 4096 * 4470)  # Kelvin*10
    tempC10 = tempK10 - 2732
    return str(tempC10 // 10) + "." + str(tempC10 % 10)

# account for voltage divider of 115k over 56k on Vinput
def vin_str(adc):
    milliVolts = (adc()*171*1100*4) // (3*56*4096)
    return str(milliVolts // 1000) + "." + str(milliVolts % 1000)

# get a distance reading from maxbotix sensor
# to save power, switch on sensor, then enable, then read
def dist_str(uart,s_pwr,tx_en):
    s_pwr.value(0)
    utime.sleep_ms(160)     # boot time
    uart.readline()         # flush bootup message
    tx_en.value(1)
    utime.sleep_ms(500)     # wait for 3 or so readings
    tx_en.value(0)
    val_str = uart.readline()
    s_pwr.value(1)
    if val_str:
        vals = [int(s[1:]) for s in val_str.split()]
        dist = sum(vals) // len(vals)
    else:
        dist = None
    return str(dist)

def sw_str(switch):
    if switch.value() == 0:
        return "1"
    else:
        return "0"

#setup 
wipy.heartbeat(False)
p_usr = Pin('GP16', mode=Pin.OUT)
p_usr.value(1)		# turn off user LED

sw_hi = Pin('GP23', mode=Pin.IN, pull=Pin.PULL_UP)
sw_lo = Pin('GP24', mode=Pin.IN, pull=Pin.PULL_UP)

adc = machine.ADC()
vin = adc.channel(pin='GP3')
temperature = adc.channel(pin='GP5')

s_pwr = Pin('GP4', mode=Pin.OUT)
s_pwr.value(1)
tx_en = Pin('GP10', mode=Pin.OUT)
tx_en.value(0)
uart = machine.UART(1,baudrate=9600,pins=(None,'GP31',None,None))

pubCount = 0
nextCount = pubCount

# setup RTC interrupt handler to publish once every period
rtc = machine.RTC()
rtc_i = rtc.irq(trigger=machine.RTC.ALARM0, handler=publish_handler, wake=machine.SLEEP)
rtc.alarm(time=6000, repeat=True)

#open client
c = MQTTClient(brdName,"mqtt")
c.connect()
print("connecting to broker")

utime.sleep(1)

while True:
    c.publish(brdName+"/iter",str(pubCount))
    c.publish(brdName+"/temp",ad592_str(temperature))
    c.publish(brdName+"/vin",vin_str(vin))
    c.publish(brdName+"/dist",dist_str(uart,s_pwr,tx_en))
    c.publish(brdName+"/sw_hi",sw_str(sw_hi))
    c.publish(brdName+"/sw_lo",sw_str(sw_lo))
    nextCount += 1
    while nextCount > pubCount:
        machine.lightsleep()

utime.sleep(1)
c.disconnect()
