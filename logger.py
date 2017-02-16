# basic data logger using WiPy
# Niall Parker, 7apr2016
import socket
import binascii
import time

import machine
from machine import RTC
from machine import Pin
from machine import ADC

import wipy

brdName = "wipy"

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

# returns temperature in degree C from LM35 as string
def lm35C_str(adc):
    milliVolts = (adc()*1100*4) // (3 * 4096)
    return str(milliVolts // 10) + "." + str(milliVolts % 10)

# account for voltage divider of 115k over 56k on Vinput
def vin_str(adc):
    milliVolts = (adc()*171*1100*4) // (3*56*4096)
    return str(milliVolts // 1000) + "." + str(milliVolts % 1000)

#setup 
wipy.heartbeat(False)
p_usr = Pin('GP16', mode=Pin.OUT)
p_usr.value(1)		# turn off user LED

adc = ADC()
vin = adc.channel(pin='GP3')
lm35 = adc.channel(pin='GP5')

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
    s.send(mtpPub(brdName+"/temp",lm35C_str(lm35)))
    s.send(mtpPub(brdName+"/vin",vin_str(vin)))
    nextCount += 1
    while nextCount > pubCount:
        machine.idle()
