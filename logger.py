# basic data logger using WiPy
# fork for esp2866 modules
# Niall Parker, 7apr2016
import socket
import time
import machine
import os

mch = os.uname().machine
uniq = machine.unique_id()
if 'ESP8266' in mch:
    if uniq[0] == 0x5d:
        brdName = 'esp12a'
    else:
        brdName = 'esp12b'
else:
    print("Board not recognized, for ESP2866 only now")
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

# account for voltage divider of 115k over 56k on Vinput
def vin_str(adc):
    milliVolts = (adc()*171*1100*4) // (3*56*4096)
    return str(milliVolts // 1000) + "." + str(milliVolts % 1000)

#setup 
p_usr = machine.Pin(13, mode=machine.Pin.OUT)
p_usr.value(0)
adc = machine.ADC(0)
vin = adc.read

pubCount = 0
nextCount = pubCount

# setup interrupt handler to publish once every period
tmr = machine.Timer(-1)
tmr.init(period=10000, mode=machine.Timer.PERIODIC, callback=publish_handler)

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
    s.send(mtpPub(brdName+"/vin",vStr))
    nextCount += 1
    while nextCount > pubCount:
        machine.idle()
