# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)
import machine
cause = machine.reset_cause()
if (cause == machine.PWRON_RESET) or (cause == machine.DEEPSLEEP_RESET):
    exec(open('logger.py').read())
else:
    import gc
    import webrepl
    webrepl.start()
    gc.collect()
