from configparser import RawConfigParser
import concurrent.futures
import os
import RPi.GPIO as GPIO
import time
from Lights_v4 import Lights
from Nextion_v4 import Nextion
from Sensors_v4 import Temperature, Humidity, Lux


# noinspection PyMethodMayBeStatic,PyUnusedLocal,SpellCheckingInspection
class Console:

    def __init__(self):
        self.config = RawConfigParser()
        self.config_file = '/home/pi/Console/console_config_v4.ini'
        self.config.read(self.config_file)
        self.config_data = str
        self.auto_headlights_mode = int()
        self.console_state = self.config['Console']['state']
        self.received_command = ''
        self.received_value = ''
        self.console_commands = {  # 'Auto_Headlights': {'command': self.auto_headlights_mode},
                                    'Threshold': {'command': self.update_threshold},
                                    'Restart': {'command': self.restart_console},
                                    'Shutdown': {'command': self.shutdown_console},
                                }
        self.headlights_state = self.config.get('Console', 'threshold_setting')
        self.interior_temperature = []
        self.exterior_temperature = []
        self.interior_humidity = []
        self.exterior_humidity = []
        self.args = []
        self.current_lux = 0
        self.current_auto_headlights_lux_threshold = self.config['Console']['threshold_setting']
# Dictionary to map data to the appropriate Nextion field and type for update
        self.nextion_data_map = {'interior_temperature': {'config_data': self.config['Environmental_Data']['interior_temperature'], 'nextion_field': 'InTemp.txt="', 'type': 'txt'},
                                 'exterior_temperature': {'config_data': self.config['Environmental_Data']['exterior_temperature'], 'nextion_field': 'OutTemp.txt="', 'type': 'txt'},
                                 'interior_humidity': {'config_data': self.config['Environmental_Data']['interior_humidity'], 'nextion_field': 'InHumid.txt="', 'type': 'txt'},
                                 'exterior_humidity': {'config_data': self.config['Environmental_Data']['exterior_humidity'], 'nextion_field': 'OutHumid.txt="', 'type': 'txt'},
                                 'headlights_threshold': {'config_data': self.config['Console']['threshold_setting'], 'nextion_field': 'Settings.thold.val=', 'type': 'int'},
                                 'headlights_auto': {'config_data': self.config['Console']['auto_headlights_mode'],'nextion_field': 'ahenable.val=', 'type': 'int'},
                                 'headlights_state': {'config_data': self.config.get('Console', 'headlights_state'),'nextion_field': 'headlights.picc=', 'type': 'int'},
                                 }
        self.last_nextion_field_initialized = None
# Currently unused
    def read_config(self):
        self.config.read(self.config_file)

# Command from Nextion to reboot host
    def restart_console(self, value):
        if value == "True":
            os.system("sudo shutdown -r now")

# Command from Nextion to shutdown host
    def shutdown_console(self, value):
        if value == "True":
            os.system("sudo shutdown -h now")

# Command from Nextion to update config with new value from Nextion if different from current value
    def update_threshold(self, value):
        if value != self.current_auto_headlights_lux_threshold:
            section = 'Console'
            option = 'threshold'
            optionb = 'setting'
            self.current_auto_headlights_lux_threshold = [section, option, optionb, value]
            self.update_config_file(self.current_auto_headlights_lux_threshold)

# Modify data stored in data file "config file" - var data stored in data file once sensor reading is completed
    def update_config_file(self, data):
        section = data[0]
        option = data[1] + '_' + data[2]
        value = data[3]
        self.config[section][option] = value
        with open(self.config_file, 'w') as config_file:
            self.config.write(config_file)
            time.sleep(5)
            config_file.close()
            self.config.read(self.config_file)
        self.update_nextion_data()

# Send data from data file to Nextion for display update
    def update_nextion_data(self):
        nextion = Nextion()
        for v in self.nextion_data_map.values():
            print('Updating Nextion')
        # Integers sent to Nextion int fields sent as plain text
            if v['type'] == 'int':
                self.config.read(self.config_file)
                field = v['nextion_field']
                int_data = v['config_data']
                if field == self.last_nextion_field_initialized:
                    break
                else:
                    self.last_nextion_field_initialized = field
                    nextion.nextion_write(field, int_data)
        # Text sent to Nextion txt fields must be wrapped in quotes
            elif v['type'] == 'txt':
                self.config.read(self.config_file)
                field = v['nextion_field']
                txt_data = (str(str(v['config_data']) + '"'))
                if field == self.last_nextion_field_initialized:
                    break
                else:
                    self.last_nextion_field_initialized = field
                    nextion.nextion_write(field, txt_data)

# Auto headlights control function called everytime Lux sensor is read and new value has been written to data file
    def auto_headlights(self):
# Read GPIO to get the current state of the headlights relay
        current_hl_state = GPIO.input(lights.head_lights_pin)
        c_lux = int(self.current_lux)
        threshold = int(self.current_auto_headlights_lux_threshold)
# Day - Check to see if lights are on, if so turn off
        if current_hl_state == 1 and c_lux > threshold:
            self.headlights_state = 'Console', 'headlights', 'state', 4
            lights.turn_light_off(lights.head_lights_pin)
            self.headlights_state = tuple(self.headlights_state)
            self.update_config_file(self.headlights_state)
# Night - Check to see if lights are off, if so turn on
        elif current_hl_state == 0 and c_lux <= threshold:
            self.headlights_state = 'Console', 'headlights', 'state', 0
            lights.turn_light_on(lights.head_lights_pin)
            self.headlights_state = tuple(self.headlights_state)
            self.update_config_file(self.headlights_state)




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
# Read environmental sensors
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
#            self.config.read(self.config_file)
            state = self.config['Console']['state']
            if state == 'initializing':
                n = 1
                break
            elif state == 'running':
                time.sleep(5)

    def get_lux_data(self):
        lux = Lux()
        section = 'Environmental_Data'
        n = 0
        while n == 0:
            print('Lux')                                                # Debugging
            self.config.read(self.config_file)
            previous_lux = self.config['Environmental_Data']['current_lux']
            self.current_lux = lux.get_lux()
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
            self.read_config()
            self.update_nextion_data()


    def console_initialize(self):
        self.config['Console']['state'] = 'initializing'
        with open(self.config_file, 'w') as config_file:
            self.config.write(config_file)
            config_file.close()
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

        self.update_nextion_data()



console = Console()
lights = Lights()
console.console_initialize()
time.sleep(5)
console.config.set('Console', 'state', 'running')
with open(console.config_file, 'w') as config_file:
    console.config.write(config_file)

console.console_run()

