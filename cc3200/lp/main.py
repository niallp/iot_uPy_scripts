# main.py -- put your code here!
import autoconfig
import micropython

micropython.alloc_emergency_exception_buf(100)

autoconfig.wlan()

execfile("logger.py")
