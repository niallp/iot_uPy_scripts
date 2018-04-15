import machine
import math
import network
import os
import time
import utime
from machine import RTC
from machine import SD
from machine import Timer
from L76GNSS import L76GNSS
from pytrack import Pytrack
from mqtt import MQTTClient
from pycom import rgbled

# setup as a station (in boot.py)

from boardCfg import brdName   # name and userID
from boardCfg import userToken

import gc

time.sleep(2)
gc.enable()

# setup rtc
rtc = machine.RTC()
rtc.ntp_sync("pool.ntp.org")
utime.sleep_ms(750)
print('\nRTC Set from NTP to UTC:', rtc.now())
utime.timezone(-25200)
print('Adjusted from UTC to PDT timezone', utime.localtime(), '\n')
py = Pytrack()
l76 = L76GNSS(py, timeout=30)
chrono = Timer.Chrono()
chrono.start()
# mqtt via thingsboard
client = MQTTClient(brdName,"thingsboard",keepalive=30,user=userToken,password='')
client.connect()
#sd = SD()
#os.mount(sd, '/sd')
#f = open('/sd/gps-record.txt', 'w')
while (True):
    coord = l76.coordinates()
    #f.write("{} - {}\n".format(coord, rtc.now()))
    if coord == (None,None):
        rgbled(0x0f0000)
    else:
        rgbled(0x000f00)
    print("{} - {} - {}".format(coord, rtc.now(), gc.mem_free()))
    if coord != (None,None):
        client.publish(topic="v1/devices/me/telemetry",msg="{'latitude' : "+str(coord[0])+ ", 'longitude' : "+str(coord[1]) + "}")
    rgbled(0)
    time.sleep(5)
