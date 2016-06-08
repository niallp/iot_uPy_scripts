# basic data logger using WiPy
# Niall Parker, 7apr2016
import socket
import binascii
import time

import machine
from machine import RTC
from machine import Pin

import wipy

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
def publish_handler (rtc_o):
    global pubCount
    p_usr.value(0)
    pubCount += 1
    #s.send(mtpPub("wipy1",b"Iter:"+str(pubCount)))
    p_usr.value(1)
    machine.sleep()

#setup 
wipy.heartbeat(False)
p_usr = Pin('GP16', mode=Pin.OUT)
p_usr.value(1)		# turn off user LED

pubCount = 0

# setup RTC interrupt handler to publish once a minute
rtc = machine.RTC()
rtc_i = rtc.irq(trigger=RTC.ALARM0, handler=publish_handler, wake=machine.SLEEP)
rtc.alarm(time=10000, repeat=True)

#open socket and send first message
addr = socket.getaddrinfo("pogoplug",1883)[0][4]
s = socket.socket()
s.connect(addr)
s.send(mtpConnect("wipy1"))

time.sleep(2)

s.send(mtpPub("wipy1",b"starting:"+str(pubCount)))

machine.sleep()
