"""\
WLAN autoconfiguration

- try to connect to a configured AP (as STA)
- fall back to AP mode
"""
from network import WLAN
import time

def wlan():
    """Connect in STA mode, fallback to AP"""
    try:
        import wlanconfig
    except ImportError:
        print('WLAN: no wlanconfig.py')
        wlanconfig = None
        wlan = WLAN(mode=WLAN.AP)
    except Exception as e:
        print('WLAN: error in wlanconfig.py: {}'.format(e))
        wlanconfig = None
        wlan = WLAN(mode=WLAN.AP)
    else:
        try:
            # configure the WLAN subsystem in station mode (the default is AP)
            wlan = WLAN()
            wlan.init(WLAN.STA)
            print('WLAN: connecting to network (AP)...')
            nets = wlan.scan()
            wlan.connect(wlanconfig.ssid, auth=None, bssid=nets[0].bssid, timeout=2000)
            print('WLAN: waiting for IP...')
            for tries in range(50):
                if wlan.isconnected():
                    print('''\
WLAN: connected!
      WiPy IP: {}
      NETMASK: {}
      GATEWAY: {}
      DNS:     {}'''.format(*wlan.ifconfig()))
                    break
                time.sleep_ms(100)
        except OSError:
            print('WLAN: found no router, going into AP mode instead')
            wlanconfig = None
        except Exception as e:
            print('WLAN: error: {}'.format(e))
            wlanconfig = None
    if wlanconfig is None:
        import machine
        machine.deepsleep(10000)
        # following should not execute
        print('No AP found, starting our own ...')
        wlan.init(mode=WLAN.AP, ssid='launchpad', auth=None, channel=7)



