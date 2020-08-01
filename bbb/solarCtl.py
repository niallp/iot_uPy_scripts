import paho.mqtt.client as mqtt
import time

import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC

def relay_message(client, userdata, message):
    msg_str = str(message.payload.decode("utf-8"))
    print("topic=",message.topic,"msg=",msg_str)
    if msg_str == "0" or msg_str == "off":
        client.publish("eastern/relayEcho","off")
    else:
        client.publish("eastern/relayEcho","on")

client = mqtt.Client("BBB")
client.on_message = relay_message
client.connect("mqtt")

client.loop_start()
client.subscribe("eastern/relay")

# for thingsboard logging
clientTB = mqtt.Client("BBBtb")
clientTB.username_pw_set(username="7k9nGbcBYONw8PehZb3k",password="")
ADC.setup()

while 1:
    batt = ADC.read_raw("AIN5")*63.219/4096
    batt_half = ADC.read_raw("AIN3")*32.193/4096
    batt_1 = ADC.read_raw("AIN1")*8.050/4096
    tbMsg = "{{\"battery\" : {:6.3f}, \"batt_half\" : {:6.3f}, \"batt_one\" : {:5.3f}}}".format(batt,batt_half,batt_1)
    clientTB.publish("v1/devices/me/telemetry",tbMsg)
    msg = "{:6.3f}".format(batt)
    client.publish("eastern/voltage",msg)
    sleep(60)
