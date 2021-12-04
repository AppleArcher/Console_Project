from configparser import ConfigParser

import serial


class Nextion:
    def __init__(self):
        self.serial = serial.Serial(port="/dev/ttyS0", baudrate=9600, timeout=None)
        self.last_nextion_field_initialized = None
        self.command_received = str
        self.command_value = str
        self.config = ConfigParser()
        #self.receive_serial_data()

    def nextion_end(self):
        self.serial.write(bytearray([0xFF, 0xFF, 0xFF]))

    def receive_serial_data(self):
        try:
            while True:
                if self.serial.in_waiting:
                    # Prefix Bytes Direct the incoming serial data to the right module
                    data_bytes = self.serial.read_until(b"*")
                    print(data_bytes)
                    if b"\x1a\xff\xff\xff" in data_bytes:
                        data_bytes = data_bytes.strip(b'\x1a\xff\xff\xff')
                        print("Stripped Bytes", data_bytes)
                    received_data = data_bytes.decode('utf-8')
                    if "!" in received_data:
                        received_data = received_data.split("!")
                        self.command_received = received_data[0]
                        self.command_value = received_data[1]
                self.serial.reset_input_buffer()
        except KeyboardInterrupt:
            print("Quit")


    def nextion_reset(self):
        r = 'rest'
        self.serial.write(str.encode(r, "utf-8"))
        self.nextion_end()

    def nextion_write(self, field, data):
        #x = bytes('"', 'utf-8')
        next_field = str.encode(field, "utf-8")
        next_data = str.encode(str(data), "utf-8")
        print('Nextion Writing')
        self.serial.write(next_field + next_data)
        self.nextion_end()
        self.serial.reset_output_buffer()



