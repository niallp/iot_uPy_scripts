import time
import ntptime

ntptime.host = "1.ca.pool.ntp.org"

from umqtt_simple import MQTTClient

from boardCfg import brdName
from boardCfg import adcScl
from boardCfg import userToken
from netConfig import mqttHost
from boardCfg import mqttHost2
from boardCfg import mqttTopic2
from boardCfg import highPin
from boardCfg import lowPin
from boardCfg import oneWirePin
from boardCfg import dhtPin
from boardCfg import sht30Pins
from boardCfg import minTime
from boardCfg import nomVolts

def unixTimeMs():
# uPython epoch is 1jan2000, not 1jan1970
    return str((time.time()+946684800)*1000)

def sawtooth(c,n):
    c.connect()
    for l in range(n):
        msg = "{'ts': "+unixTimeMs()+",'values': {'test1' :"+str(l%10)+"}}"
        c.publish("v1/devices/me/telemetry",msg)
        msg2 = "{'test2' :"+str(l%10)+"}"
        c.publish("v1/devices/me/telemetry",msg2)
        time.sleep(1)
    c.disconnect()

try:
    ntptime.settime()
    syncTime = time.time()
    print("time set to NTP")
except OSError:
    print("OSError: ", str(OSError))

c = MQTTClient(brdName,mqttHost,keepalive=30,user=userToken,password='')

print("RTC,NTP,RTC-NTP")

for i in range(10):
    deltaRTC = time.time()-syncTime
    deltaNTP = ntptime.time()-syncTime
    print(deltaRTC,deltaNTP,deltaRTC-deltaNTP)
    sawtooth(c,10)
    time.sleep(590)
