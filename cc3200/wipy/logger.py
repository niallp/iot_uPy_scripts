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

brdName = 'wipy'
userToken = 'z7Z1HA8P3JUou9N4o51m'  # for thingsboard

# for periodic publishing
def publish_handler(rtc_o):
    global pubCount
    p_usr.value(0)
    pubCount += 1
    p_usr.value(1)

# returns temperature in degree C from AD592 as string
def ad592_str(adc):
    milliVolts = (adc()*1494) // 4096
    tempK10 = (milliVolts*10000) // 4460      # Kelvin*10, 4k46 Rsense
    tempC10 = tempK10 - 2732
    return str(tempC10 // 10) + "." + str(tempC10 % 10)

# account for voltage divider of 115k over 56k on Vbatt (on expansion board)
# calibrated against MS8209 DVM, np 16may2020
def vbatt_str(adc):
    milliVolts = (adc()*4722) // 4096
    return str(milliVolts // 1000) + "." + str(milliVolts % 1000)

# get a distance reading from maxbotix sensor
# to save power, switch on sensor, then enable, then read
def dist_str(uart,s_pwr,tx_en):
    s_pwr.value(0)
    utime.sleep_ms(160)     # boot time
    uart.readline()         # flush bootup message
    tx_en.value(1)
    utime.sleep_ms(1500)     # wait for some readings
    #tx_en.value(0)         ... keep free running, noise ?
    val_str = uart.readline()
    s_pwr.value(1)
    if val_str:
        vals = [int(s[1:]) for s in val_str.split()]
        if len(vals) > 42:
            dist = sum(vals[:42]) // 42
        else:
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

sw_hi = Pin('GP24', mode=Pin.IN, pull=Pin.PULL_UP)
sw_lo = Pin('GP11', mode=Pin.IN, pull=Pin.PULL_UP)

adc = machine.ADC()
vbatt = adc.channel(pin='GP3')
temperature = adc.channel(pin='GP5')

s_pwr = Pin('GP4', mode=Pin.OUT)
s_pwr.value(1)      # start powered off
tx_en = Pin('GP10', mode=Pin.OUT)
tx_en.value(1)      # keep enabled now
uart = machine.UART(1,baudrate=9600,pins=(None,'GP31',None,None))

pubCount = 0
nextCount = pubCount

# setup RTC interrupt handler to publish once every period
rtc = machine.RTC()
rtc_i = rtc.irq(trigger=machine.RTC.ALARM0, handler=publish_handler, wake=machine.SLEEP)
rtc.alarm(time=30000, repeat=True)

# allow wakeup with switch inputs as well (faster response)
# note only last enabled interrupt active for machine.SLEEP
# need to go to DEEPSLEEP and restart to permit multiple pins
# interrupts not used 11oct2021: too many false triggers ?
# poll faster instead, every 30 seconds
#sw_hi.irq(handler=publish_handler, trigger=Pin.IRQ_FALLING, wake=machine.SLEEP)
#sw_lo.irq(handler=publish_handler, trigger=Pin.IRQ_FALLING, wake=machine.SLEEP)

#open client for local access (controller, node-red)
c = MQTTClient(brdName,"mqtt",keepalive=60)
#open 2nd connection for datalogging in thingsboard
tb = MQTTClient(brdName,'lutze.balsk',keepalive=30,user=userToken,password='')
utime.sleep(1)

while True:
    try:
        c.connect()
        print("connected to mqtt")
        tb.connect()
        print("connected to thingsboard")
        # buffer this measurement, take time (serial)
        dist_s = dist_str(uart,s_pwr,tx_en)
        c.publish(brdName+"/iter",str(pubCount))
        c.publish(brdName+"/temp",ad592_str(temperature))
        c.publish(brdName+"/volts",vbatt_str(vbatt))
        c.publish(brdName+"/dist",dist_s)
        c.publish(brdName+"/sw_high",sw_str(sw_hi))
        c.publish(brdName+"/sw_low",sw_str(sw_lo))
        tb_msg = "{{'volts' : {}, 'temperature' : {}, 'level' : {}, 'sw_high' : {}, 'sw_low' : {} }}".format(vbatt_str(vbatt),ad592_str(temperature),dist_s,sw_str(sw_hi),sw_str(sw_lo))
        tb.publish("v1/devices/me/telemetry",tb_msg)
        nextCount += 1
        c.disconnect()
        tb.disconnect()
    except OSError:
        print("OError, reset in 30 seconds")
        utime.sleep(30)
        machine.reset()
    except:
        print("other errors, resetting")
        utime.sleep(60)
        machine.reset()
    while nextCount > pubCount:
        machine.lightsleep()

print("Exited logger")
