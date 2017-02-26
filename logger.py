# basic data logger using WiPy
# Niall Parker, 7apr2016
import socket
import binascii
import time

import machine
from machine import RTC
from machine import Pin
from machine import ADC
from machine import I2C

import os
import wipy

mch = os.uname().machine
if 'LaunchPad' in mch:
    uniq = machine.unique_id()
    if uniq[5] == 0xfe:
        brdName = 'lp2'
    else:
        brdName = 'lp1'
    isWiPy = False
    TMP006 = 0x41       # i2c address
    DIE_T = 0x01        # die temperature register
elif 'WiPy' in mch:
    brdName = 'wipy'
    isWiPy = True
else:
    print("Board not recognized")
    raise SystemExit

# mqtt publish fcns from mqtt-publish.py (github, GPL v 2)
def mtStr(s):
  return bytes([len(s) >> 8, len(s) & 255]) + s.encode('utf-8')

def mtPacket(cmd, variable, payload):
  return bytes([cmd, len(variable) + len(payload)]) + variable + payload

def mtpConnect(name):
  return mtPacket(
           0b00010000,
           mtStr("MQTT") + # protocol name
           b'\x04' +       # protocol level
           b'\x00' +       # connect flag
           b'\xFF\xFF',    # keepalive
           mtStr(name)
  )

def mtpDisconnect():
  return bytes([0b11100000, 0b00000000])

def mtpPub(topic, data):
  return  mtPacket(0b00110001, mtStr(topic), data)

# for periodic publishing
def publish_handler(rtc_o):
    global pubCount
    p_usr.value(0)
    pubCount += 1
    p_usr.value(1)

# returns temperature string in C from TMP006 (die temperature
def tmp006_str(i2c):
    data = i2c.readfrom_mem(TMP006,DIE_T,2)
    degC = (data[0] << 1) + (data[1] >> 7)
    degC_32nd = (data[1] & 0x7f) >> 2       # 32nds of degrees
    return str(degC) + "." + str((degC_32nd*10 + 16) >> 5)

# returns temperature in degree C from LM35 as string
def lm35C_str(adc):
    milliVolts = (adc()*1100*4) // (3 * 4096)
    return str(milliVolts // 10) + "." + str(milliVolts % 10)

# account for voltage divider of 115k over 56k on Vinput
def vin_str(adc):
    milliVolts = (adc()*171*1100*4) // (3*56*4096)
    return str(milliVolts // 1000) + "." + str(milliVolts % 1000)

#setup 
wipy.heartbeat(False)       # use as debug LED (manually)

p_usr = Pin('GP16', mode=Pin.OUT)
p_usr.value(1)		# turn off user LED (not on LP)
adc = ADC()
vin = adc.channel(pin='GP3')

if isWiPy:
    lm35 = adc.channel(pin='GP5')
else:
    i2c_pins = ('GP11','GP10')
    i2c = I2C(mode=I2C.MASTER, baudrate=1000000, pins=i2c_pins)
    devices = i2c.scan()
    if not 65 in devices:    # TMP006 at address 64 (0x41) by default
        raise SystemExit
    
pubCount = 0
nextCount = pubCount

# setup RTC interrupt handler to publish once every period
rtc = machine.RTC()
rtc_i = rtc.irq(trigger=RTC.ALARM0, handler=publish_handler, wake=machine.IDLE)
rtc.alarm(time=10000, repeat=True)

#open socket and send first message
addr = socket.getaddrinfo("pogoplug",1883)[0][4]
s = socket.socket()
s.connect(addr)
s.send(mtpConnect(brdName))

time.sleep(1)

s.send(mtpPub(brdName,b"starting:"+str(pubCount)))

while True:
    s.send(mtpPub(brdName+"/iter",str(pubCount)))
    vStr = vin_str(vin)
    if isWiPy:
        tStr = lm35C_str(lm35)
    else:
        tStr = tmp006_str(i2c)
    s.send(mtpPub(brdName+"/temp",tStr))
    s.send(mtpPub(brdName+"/vin",vStr))
    nextCount += 1
    while nextCount > pubCount:
        machine.idle()
