# mqtt publish fcns from mqtt-publish.py (github, GPL v 2)
def mqstr(s):
  return bytes([len(s) >> 8, len(s) & 255]) + s.encode('utf-8')

def packet(cmd, variable, payload):
  return bytes([cmd, len(variable) + len(payload)]) + variable + payload

def connect(name):
  return packet(
           0b00010000,
           mqstr("MQTT") + # protocol name
           b'\x04' +       # protocol level
           b'\x00' +       # connect flag
           b'\xFF\xFF',    # keepalive
           mqstr(name)
  )

def disconnect():
  return bytes([0b11100000, 0b00000000])

def pub(topic, data):
  return  packet(0b00110001, mqstr(topic), data)

