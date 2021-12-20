IoT scripts, mostly in uPython
========================
<p align="center">
  <img src="https://cloud.githubusercontent.com/assets/7749335/6927441/bdb84f70-d7ed-11e4-96c8-9dd8dda12857.png" alt="The WiPy Logo"/>
</p>

Most code on thingsboard branch

uses a netConfig.py file to hold wifi credentials, should auto connect to strongest AP it knows about.

Components in this repository:
- cc3200/ -- for WiPy and TI Launchpad hardware
- esp32/ -- esp32 specific code (FiPy)
- esp8266/ -- for ESP01, ESP12 and WeMOS d1 modules
