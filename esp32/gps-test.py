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

# setup as a station (in boot.py)

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
# mqtt via local first
client = MQTTClient("fipy1","mqtt")
client.connect()
#sd = SD()
#os.mount(sd, '/sd')
#f = open('/sd/gps-record.txt', 'w')
while (True):

    coord = l76.coordinates()
    #f.write("{} - {}\n".format(coord, rtc.now()))
    print("{} - {} - {}".format(coord, rtc.now(), gc.mem_free()))
    client.publish(topic="fipy/lat",msg=str(coord[0]))
    client.publish(topic="fipy/lng",msg=str(coord[1]))
