# This file is executed on every boot (including wake-boot from deepsleep)
import time
'''
from __init__ import Logger
from __init__ import CRITICAL
from __init__ import ERROR
from __init__ import WARNING
from __init__ import INFO
from __init__ import DEBUG 
from __init__ import NOTSET
'''
# should now try strongest ap it knows about, default to balskG

def do_connect(maxRetry):
    retry = 0
    import network
    from utime import sleep_ms
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)

    if not sta_if.isconnected():
        bssid = None
        pwd = None
        nets = sta_if.scan()
        nets.sort(key=lambda net: net[3], reverse=True)     # strongest first
        from netConfig import known_nets
        for net in nets:
            ssid = net[0].decode('utf-8')
            #logger.info("ssid:"+ssid)
            print("ssid: "+ssid)
            if ssid in known_nets:
                bssid = net[1]
                #RSSI = net[3]
                if bssid == b'\xc0J\x00,\xb1\x8d':
                    #logger.warning('skip bssid '+str(bssid))
                    print('skip bssid '+str(bssid) )
                else:
                    pwd = known_nets[ssid]['pwd']
                    break
            else:
                #logger.warning(ssid+' is unknown')
                print(ssid+'is unknown')
        #logger.info('connecting to network '+ssid+' BSSID: '+str(bssid))
        print('connecting to network '+ssid+' BSSID: '+str(bssid))
        if bssid == None:
            print('bssid = None')
            #logger.warning("bssid = None")
            #sta_if.connect(ssid,pwd)
        else:
           sta_if.connect(ssid,pwd,bssid=bssid)
           while (not sta_if.isconnected() and retry < maxRetry):
               #waiting for connection
               retry = retry + 1
               print('retry {}'.format(retry))
               #logger.info('retry {}'.format(retry))
               sleep_ms(500)
    else:
        #logger.info("connected already")
        print("connected already")
    #logger.info("network config:"+ str(sta_if.ifconfig()))
    print("network config: "+ str(sta_if.ifconfig()))
    ma = sta_if.config('mac')
    print("mac address: " + hex(ma[0]),hex(ma[1]),hex(ma[2]),hex(ma[3]),hex(ma[4]),hex(ma[5]),)
    return sta_if.isconnected()



import esp
esp.osdebug(None)
import machine
#dbgSel = machine.Pin(14,machine.Pin.IN,machine.Pin.PULL_UP)
'''
import __init__ 

if(0):
    __init__.basicConfig(level=INFO, filename='log')
    global logger
    logger = __init__.getLogger('log')
    logger.setLevel(CRITICAL)
else:
    global logger
    logger = __init__.getLogger()
    logger.setLevel(CRITICAL)
'''
#printout = "Start: " + str(time.localtime())
#print(printout)
#logger.critical( "Start Logging: " + str(time.localtime()) ) 


if (0):   #cause != machine.DEEPSLEEP_RESET):
    # give user a chance to intervene
    print('Starting debug mode');
    do_connect(99)
    import gc
    import webrepl
    webrepl.start()
    gc.collect()
else:
    if (not do_connect(30)):   # network failed, go back to sleep for 5 minutes
        #logger.warning('network failed, deep sleeping')
        
        import netConfig
        from netConfig import wifiConnected
        print("connected: False? " + str(netConfig.wifiConnected))


        #machine.deepsleep(4200000)
        #machine.deepsleep(60000)
    else:
        #logger.info('starting')
        
        
        import netConfig
        from netConfig import wifiConnected
        print("connected: " + str(netConfig.wifiConnected))
        netConfig.wifiConnected = True
        print("connected: True? " + str(netConfig.wifiConnected))

        print('starting')
        
        #exec(open('logger.py').read())
