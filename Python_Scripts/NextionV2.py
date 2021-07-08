import time
import serial
from configparser import ConfigParser

config = ConfigParser()
config.read('console_config.ini')

ser = serial.Serial(port="/dev/ttyS0", baudrate=9600, timeout=None)
command_data = []
data_value = ''

# Nextion data termination
def end():
    ser.write(bytearray([0xFF, 0xFF, 0xFF]))

# Nextion data write O is Nextion Object Name, T is Object text data
def write(field, data):
    x = bytes('"', 'utf-8')
    next_field = str.encode(field, "utf-8")
    next_data = str.encode(data, "utf-8")
    ser.write(next_field + next_data)
    end()

def receive_data():
    try:
        while True:
            if ser.in_waiting:
                prefix_bytes = ser.read_until(b"*")
                print(prefix_bytes)
                if b"\x1a\xff\xff\xff" in prefix_bytes:
                    prefix_bytes = prefix_bytes.strip(b'\x1a\xff\xff\xff')
                    print("Stripped Bytes", prefix_bytes)
                rcv_buffer = ser.read_until(b"!")
                rcv_split = rcv_buffer.split(b"*")
                key_bytes = rcv_split[0]
                value_bytes = rcv_split[1]

                data_prefix = prefix_bytes.decode('utf-8')
                data_prefix = data_prefix.strip('*')
                data_key = key_bytes.decode('utf-8')

                if value_bytes is not None:
                    data_value = value_bytes.decode('utf-8')
                    data_value = data_value.strip('!')
                else:
                    data_value = None
                ser.reset_input_buffer()
                command_data.append(data_prefix)
                command_data.append(data_key)
                print('Command Data', command_data)
                return command_data
        else:
            print('Command Not Found')
            time.sleep(.1)
    except KeyboardInterrupt:
        print("Quit")


def nextion_reset():
    r = 'rest'
    ser.write(str.encode(r, "utf-8"))
    end()

#def decode_data(prefix, key, value):
#    print('Decoding Data')
#    if prefix == 'Consol':
#        print('Console Command Decoded')
#        decode_commands(key, value)
#    elif prefix == 'Lights':
#        print('Lights Command Decoded')
#
#    time.sleep(3)
#    decode_commands(key)

