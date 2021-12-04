import configparser
import concurrent.futures
import os
import RPi.GPIO as GPIO
import time
from Lights_v3 import Lights
from Nextion_v3 import Nextion
from Sensors_v2 import *





class Console:

    def __init__(self):
        self.config = configparser.RawConfigParser()
        self.config_file = '/home/pi/Projects/Console_Project/Application/Learning_New_Things/console_config.ini'
        self.config.read(self.config_file)
        self.config_data = str
        self.auto_headlights_mode = int()
        self.auto_headlights_lux_threshold = self.config['Console']['threshold']
        self.headlights_state = self.config['Console']['headlights_state']
        self.console_state = self.config['Console']['state']
        self.received_command = ''
        self.received_value = ''
        self.console_commands = {  # 'Auto_Headlights': {'command': self.auto_headlights_mode},
                                    'Threshold': {'command': self.update_threshold},
                                    'Restart': {'command': self.restart_console},
                                    'Shutdown': {'command': self.shutdown_console},
                                }
        self.interior_temperature = []
        self.exterior_temperature = []
        self.interior_humidity = []
        self.exterior_humidity = []
        self.args = []
        self.current_lux = 0
        self.nextion_data_map = {'interior_temperature': {'data_var': self.interior_temperature, 'config_data': self.config['Environmental_Data']['interior_temperature'], 'nextion_field': 'InTemp.txt="', 'type': 'txt'},
                                 'exterior_temperature': {'data_var': self.exterior_temperature, 'config_data': self.config['Environmental_Data']['exterior_temperature'], 'nextion_field': 'OutTemp.txt="', 'type': 'txt'},
                                 'interior_humidity': {'data_var': self.interior_humidity, 'config_data': self.config['Environmental_Data']['interior_humidity'], 'nextion_field': 'InHumid.txt="', 'type': 'txt'},
                                 'exterior_humidity': {'data_var': self.exterior_humidity, 'config_data': self.config['Environmental_Data']['exterior_humidity'], 'nextion_field': 'OutHumid.txt="', 'type': 'txt'},
                                 'headlights_threshold': {'data_var': self.auto_headlights_lux_threshold, 'config_data': self.config['Console']['threshold'], 'nextion_field': 'Settings.thold.val=', 'type': 'int'},
                                 'headlights_auto': {'data_var': self.auto_headlights_mode, 'config_data': self.config['Console']['auto_headlights_mode'], 'nextion_field': 'ahenable.val=', 'type': 'int'},
                                 'headlights_state': {'data_var': self.headlights_state, 'config_data': self.config['Console']['headlights_state'], 'nextion_field': 'headlights.picc=', 'type': 'int'},
                                 }
        self.last_nextion_field_initialized = None


    def read_config(self):
        self.config.read(self.config_file)

    def restart_console(self, value):
        # Restart Console Pi
        if value == "True":
            os.system("sudo shutdown -r now")

    def shutdown_console(self, value):
        # Shutdown Console Pi
        if value == "True":
            os.system("sudo shutdown -h now")

    def update_config_file(self, data):
        section = data[0]
        option = data[1] + '_' + data[2]
        value = data[3]
        self.config.read(self.config_file)
        self.config.set(section, option, value)
        with open(self.config_file, 'w') as config_file:
            self.config.write(config_file)
            config_file.close()
        self.config.read(self.config_file)

    def update_nextion_data(self):
        nextion = Nextion()
        for v in self.nextion_data_map.values():
            self.config.read(self.config_file)
            print('Updating Nextion')                                   # Debugging
            if v['type'] == 'int':
                field = v['nextion_field']
                int_data = v['config_data']
                if field == self.last_nextion_field_initialized:
                    break
                else:
                    self.last_nextion_field_initialized = field
                    nextion.nextion_write(field, int_data)
            elif v['type'] == 'txt':
                field = v['nextion_field']
                txt_data = (str(str(v['config_data']) + '"'))
                if field == self.last_nextion_field_initialized:
                    break
                else:
                    self.last_nextion_field_initialized = field
                    nextion.nextion_write(field, txt_data)

    def update_threshold(self, value):

        # Update config with new value from Nextion
        current_threshold = self.auto_headlights_lux_threshold
        if value != current_threshold:
            self.config.set('Console', 'threshold', value)
            with open(self.config_file, 'w') as config_file:
                self.config.write(config_file)

    def auto_headlights(self):
        self.config.read(self.config_file)
        current_hl_state = GPIO.input(lights.head_lights_pin)
        new_hl_state = current_hl_state
        c_lux = int(self.current_lux)
        threshold = int(self.auto_headlights_lux_threshold)
        print('auto_headlights')                                        # Debugging
        print('Current Headlights State = ', current_hl_state)          # Debugging
        if current_hl_state == 1:
            if c_lux > threshold:
                print('Headlights are On, Turning Off')                 # Debugging
                lights.turn_light_off(lights.head_lights_pin)
                self.config.set('Console', 'headlights_state', '4')
                new_hl_state = 0
                with open(self.config_file, 'w') as config_file:
                    self.config.write(config_file)

        if current_hl_state == 0:
            if c_lux <= threshold:
                print('Headlights are Off, Turning On')                 # Debugging
                lights.turn_light_on(lights.head_lights_pin)
                self.config.set('Console', 'headlights_state', '0')
                new_hl_state = 1
                with open(self.config_file, 'w') as config_file:
                    self.config.write(config_file)
        if new_hl_state != current_hl_state:
            self.config.read(self.config_file)
            key = self.nextion_data_map['headlights_state']
            field = key['nextion_field']
            int_data = key['config_data']
            nextion = Nextion()
            nextion.nextion_write(field, int_data)

    def process_command(self):
        nextion = Nextion()
        n = 0
        while n == 0:
            nextion.receive_serial_data()
            command = nextion.nextion_received_command
            value = nextion.nextion_received_value
            print(command)                                              # Debugging
            print(value)                                                # Debugging
            state = self.config['Console']['state']
            if command in self.console_commands:
                entry = self.console_commands[str(command)]
                entry['command'](value)
            elif value == '':
                self.received_command = command
                lights.decode_command(self.received_command)
            elif state == 'initializing':
                n = 1
                break
            else:
                print('Command Not Found')
            time.sleep(.1)

    def get_enviro_data(self):

        section = 'Environmental_Data'
        n = 0
        while n == 0:
            t = Temperature()
            h = Humidity()
            print('Enviro')                                             # Debugging
            self.interior_temperature = t.get_temperature('interior')
            self.exterior_temperature = t.get_temperature('exterior')
            self.interior_humidity = h.get_humidity('interior')
            self.exterior_humidity = h.get_humidity('exterior')
            data = [self.interior_temperature, self.exterior_temperature,
                    self.interior_humidity, self.exterior_humidity]
            for i in data:
                self.args = section, i[0], i[1], i[2]
                self.args = tuple(self.args)
                self.update_config_file(self.args)
                print(i)                                                # Debugging
                time.sleep(2)
            state = self.config['Console']['state']
            if state == 'initializing':
                n = 1
                break
            elif state == 'running':
                self.update_nextion_data()
            time.sleep(10)

    def get_lux_data(self):
        lux = Lux()
        section = 'Environmental_Data'
        n = 0
        while n == 0:
            print('Lux')                                                # Debugging
            self.current_lux = lux.get_lux()
            self.config.read(self.config_file)
            previous_lux = self.config['Environmental_Data']['current_lux']
            print('PLux', previous_lux)                                 # Debugging
            print('CLux', self.current_lux)                             # Debugging
            if int(self.current_lux) != int(previous_lux):
                self.config.set(section, 'current_lux', self.current_lux)
                with open(self.config_file, 'w') as config_file:
                    self.config.write(config_file)
            self.auto_headlights()
            state = self.config['Console']['state']
            if state == 'initializing':
                n = 1
                break
            time.sleep(30)

    def console_initialize(self):
        self.config.set('Console','state', 'initializing')
        with open(self.config_file, 'w') as config_file:
            self.config.write(config_file)
        self.config.read(self.config_file)
        nextion = Nextion()
        nextion.nextion_reset()
        nextion.serial.flush()
        nextion.serial.reset_input_buffer()
        nextion.serial.reset_output_buffer()
        print('Console Initializing')
        try:
            with concurrent.futures.ThreadPoolExecutor() as console_exec:
                t1 = console_exec.submit(self.get_enviro_data)
                t2 = console_exec.submit(self.get_lux_data)
                threads = [t1, t2]
                for t in threads:
                    print(str(t), t.result())                               # Debugging
        except KeyboardInterrupt:
            print('Quit')

    def console_run(self):
        print('Console Running')                                            # Debugging
        self.update_nextion_data()
        self.config.set('Console', 'state', 'running')
        with open(self.config_file, 'w') as config_file:
            self.config.write(config_file)
        self.config.read(self.config_file)
        try:
            with concurrent.futures.ThreadPoolExecutor() as console_exec:

                t1 = console_exec.submit(self.get_enviro_data)
                t2 = console_exec.submit(self.get_lux_data)
                t3 = console_exec.submit(self.process_command)
                threads = [t1, t2, t3]
                for t in threads:
                    print(str(t), t.result)                                 # Debugging
        except KeyboardInterrupt:
            print('Quit')





console = Console()
lights = Lights()
console.console_initialize()
console.console_run()
#c.get_enviro_data()
#c.get_lux_data()
#c.auto_headlights()
#c.process_command()




