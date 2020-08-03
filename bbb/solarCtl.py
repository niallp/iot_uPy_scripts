import paho.mqtt.client as mqtt
import time

import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC

def relay_message(client, userdata, message):
    msg_str = str(message.payload.decode("utf-8"))
    print("topic=",message.topic,"msg=",msg_str)
    if msg_str == "0" or msg_str == "off":
        msg_str = "off"
        msg = 0
    else:
        msg_str = "on"
        msg = 1
    client.publish("cabin/relayEcho",msg_str)
    clientTB.publish("v1/devices/me/telemetry",'{"relay" : '+str(msg)+'}')
    relay_ctl(msg_str == "on")

def relay_ctl(flag):
    if flag and batt > 48.0:
        print("switch relay on")
        GPIO.output("P9_12", GPIO.LOW)
    else:
        print("switch relay off")
        GPIO.output("P9_12", GPIO.HIGH)

client = mqtt.Client("BBB")
client.on_message = relay_message
client.connect("mqtt-east.balsk")

client.loop_start()
client.subscribe("cabin/relay")

GPIO.setup("P9_12", GPIO.OUT)
GPIO.output("P9_12", GPIO.HIGH)

# for thingsboard logging
clientTB = mqtt.Client("BBBtb")
clientTB.username_pw_set(username="7k9nGbcBYONw8PehZb3k",password="")
clientTB.connect("thingsboard.balsk")
ADC.setup()

try:
    while 1:
        batt = ADC.read_raw("AIN5")*63.219/4096
        batt_half = ADC.read_raw("AIN3")*32.193/4096
        batt_1 = ADC.read_raw("AIN1")*8.050/4096
        tbMsg = "{{\"battery\" : {:6.3f}, \"batt_half\" : {:6.3f}, \"batt_one\" : {:5.3f}}}".format(batt,batt_half,batt_1)
        clientTB.publish("v1/devices/me/telemetry",tbMsg)
        msg = "{:6.3f}".format(batt)
        client.publish("cabin/voltage",msg)
        time.sleep(60)
except KeyboardInterrupt:
    GPIO.output("P9_12",GPIO.HIGH)
    GPIO.cleanup()
