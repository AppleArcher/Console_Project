import serial
import time





class Nextion():
    def __init__(self):
        self.serial = serial.Serial(port="/dev/ttyS0", baudrate=9600, timeout=None)
        self.last_nextion_field_initialized = None
        self.nextion_received_command = ''
        self.nextion_received_value = ''

    def nextion_end(self):
        self.serial.write(bytearray([0xFF, 0xFF, 0xFF]))

    def receive_serial_data(self):
        try:
            while True:
                if self.serial.in_waiting:
                    # Prefix Bytes Direct the incoming serial data to the right module
                    data_bytes = self.serial.read_until(b"*")
                    print(data_bytes)
                    if b"\xff\xff\xff" in data_bytes:
                        data_bytes = data_bytes.strip(b'\xff\xff\xff')
                        print("Stripped Bytes", data_bytes)
                    received_data = data_bytes.decode('utf-8')
                    received_data = received_data.strip('*')
                    print('Received Data = ', received_data)
                    if "!" in received_data:
                        print("Splitting")
                        received_data = received_data.split("!")
                        self.nextion_received_command = received_data[0]
                        self.nextion_received_value = received_data[1]
                        return self.nextion_received_command, self.nextion_received_value
                    if "!" not in received_data:
                        print("Forwarding")
                        self.nextion_received_command = received_data
                        self.nextion_received_value = ''
                        return self.nextion_received_command, self.nextion_received_value


        except KeyboardInterrupt:
            print("Quit")

        finally:
            self.serial.reset_input_buffer()

    def nextion_reset(self):
        r = 'rest'
        self.serial.write(str.encode(r, "utf-8"))
        self.nextion_end()

    def nextion_write(self, field, data):
        x = bytes('"', 'utf-8')
        next_field = str.encode(field, "utf-8")
        next_data = str.encode(str(data), "utf-8")
        self.serial.write(next_field + next_data)
        self.nextion_end()
        print('Nextion Writing - ', next_field, '', next_data)




