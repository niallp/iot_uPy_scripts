# boot.py -- run on boot-up
# can run arbitrary Python, but best to keep it minimal
import os, machine
os.dupterm(machine.UART(0, 115200))
