#!/bin/bash
if [ $# -eq 0 ]; then
	echo "Usage $0 <board> <main> <port>"
	exit 1
fi
if [ -z "$3" ]; then
	export AMPY_PORT=/dev/ttyUSB0
else
	export AMPY_PORT=/dev/tty$3
fi
if [ -z "$2" ]; then
	MAIN=logger
else
	MAIN=$2
fi
if [ -z "$1" ]; then
	echo "Need to define board to program"
	exit 2
else
	BOARD=$1
fi
echo "existing files:"
ampy ls
echo "replacing boot.py"
ampy put boot.py
echo "replacing boardCfg.py"
ampy put boardCfg_$BOARD.py boardCfg.py
echo "replacing fileQueue"
ampy put ../fileQueue.py
echo "replacing main"
ampy put $MAIN.py main.py
echo "replacing netConfig"
ampy put ../netConfig.py
echo "replacing sht30"
ampy put ../sht30.py
echo "replacing mqtt"
ampy put ../umqtt_simple.py
echo "replacing DS18B20 cal"
ampy put ../ds18B20cal.py 
