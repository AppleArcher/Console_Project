import asyncio
import os
import time
from configparser import ConfigParser

import RPi.GPIO as GPIO

from Lights_v2 import Lights
from Nextion_v2 import Nextion
from Sensors_v1 import EnvironmentalSensors
from Sensors_v1 import LuxSensor


class Console:


    def __init__(self):
        self.config = ConfigParser()
        self.config_file = '/home/pi/Projects/Console_Project/Application/V2/console_config.ini'
        self.config.read(self.config_file)
        self.config_data = str
        self.command_received = str
        self.command_value = str
        self.console_state = str(self.config['Console']['state'])

        # Environmental Data Variables
        self.interior_temperature = int()
        self.interior_humidity = int()
        self.exterior_temperature = int()
        self.exterior_humidity = int()
        self.lux = int()
        # Console Configuration Settings
        self.auto_headlights_mode = int()
        self.auto_headlights_lux_threshold = int()
        self.headlights_state = int()

        self.data_objects = {'temperature_inside': {'var': self.interior_temperature, 'nextion_field': 'InTemp.txt="', 'config': int(self.config['Environmental_Data']['interior_temperature'])},
                             'temperature_outside': {'var': self.exterior_temperature, 'nextion_field': 'OutTemp.txt="', 'config': int(self.config['Environmental_Data']['interior_humidity'])},
                             'humidity_inside': {'var': self.interior_humidity, 'nextion_field': 'InHumid.txt="', 'config': self.config['Environmental_Data'].getint('exterior_temperature')},
                             'humidity_outside': {'var': self.exterior_humidity, 'nextion_field': 'OutHumid.txt="', 'config': self.config['Environmental_Data'].getint('exterior_humidity')},
                             'headlights_threshold': {'var': self.auto_headlights_lux_threshold, 'nextion_field': 'Settings.thold.val=', 'config': self.config['Console'].getint('threshold')},
                             'headlights_auto': {'var': self.auto_headlights_mode, 'nextion_field': 'ahenable.val=', 'config': self.config['Console'].getint('auto_headlights_mode')},
                             'headlights_state': {'var': self.headlights_state, 'nextion_field': 'headlights.pic=', 'config': self.config['Console'].getint('headlights_state')},
                             'current_lux': {'var': self.lux, 'nextion_field': 'none', 'config': int(self.config['Environmental_Data']['current_lux'])},
                             }

        self.console_commands = {  # 'Auto_Headlights': {'command': self.auto_headlights_mode},
                                    'Threshold': {'command': self.update_threshold},
                                    'Restart': {'command': self.restart_console},
                                    'Shutdown': {'command': self.shutdown_console},

                                }

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

    def update_config_file(self, *args):
        section = str(args[0])
        option = str(args[1])
        value = str(args[2])
        self.config.read(self.config_file)
        self.config.set(section, option, value)
        with open(self.config_file, 'w') as config_file:
            self.config.write(config_file)
            print('Writing data to data_file -', self.config[section], {option : value})
            config_file.close()
        self.config.read(self.config_file)

    def update_threshold(self, value):
        value = value
        # Update config with new value from Nextion
        current_threshold = self.auto_headlights_lux_threshold
        if value != current_threshold:
            self.config_data = ('Console', 'threshold', value)
            self.update_config_file(self.config_data)

    def process_command(self):
        nextion = Nextion()
        lights = Lights()
        if nextion.command_received in self.console_commands:
            entry = self.console_commands[str(nextion.command_received)]
            value = self.command_value
            entry['command'](value)
        if nextion.command_received in lights.lights_commands:
            lights.decode_command(self.command_received)
        else:
            print('Command Not Found')
            time.sleep(.1)


    def update_int_temp(self):
        sensor = EnvironmentalSensors()
        self.interior_temperature = sensor.get_sensor_data('interior', 'temperature')
        time.sleep(1)
        console = Console()
        console.update_config_file('Environmental_Data', sensor.option, sensor.data_out)

    def update_ext_temp(self):
        sensor = EnvironmentalSensors()
        self.exterior_temperature = sensor.get_sensor_data('exterior', 'temperature')
        time.sleep(1)
        console = Console()
        console.update_config_file('Environmental_Data', sensor.option, sensor.data_out)

    def update_int_humidity(self):
        sensor = EnvironmentalSensors()
        self.interior_humidity = sensor.get_sensor_data('interior', 'humidity')
        time.sleep(1)
        console = Console()
        console.update_config_file('Environmental_Data', sensor.option, sensor.data_out)

    def update_ext_humidity(self):
        sensor = EnvironmentalSensors()
        self.exterior_humidity = sensor.get_sensor_data('exterior', 'humidity')
        time.sleep(1)
        console = Console()
        console.update_config_file('Environmental_Data', sensor.option, sensor.data_out)

    def update_lux(self):
        sensor = LuxSensor()
        self.lux = sensor.get_lux()
        time.sleep(5)
        console = Console()
        console.update_config_file('Environmental_Data', 'current_lux', sensor.current_lux)


    async def update_sensors(self):
        try:
            await asyncio.gather(
                asyncio.to_thread(self.update_int_temp),
            )
            time.sleep(10)

            await asyncio.gather(
                asyncio.to_thread(self.update_ext_temp)
            )
            time.sleep(2)

            await asyncio.gather(
                asyncio.to_thread(self.update_int_humidity)
            )
            time.sleep(2)

            await asyncio.gather(
                asyncio.to_thread(self.update_ext_humidity)
            )
            time.sleep(2)

            await asyncio.gather(
                asyncio.to_thread(self.update_lux)
            )
        except asyncio.TimeoutError:
            print('Timeout')

    async def auto_headlights(self):
        print('auto_headlights')
        lights = Lights()
        hl_state = GPIO.input(lights.head_lights_pin)
        threshold = int(self.auto_headlights_lux_threshold)
        while True:
            if self.lux <= threshold and hl_state == 1:
                break
            elif self.lux <= threshold and hl_state == 0:
                lights.turn_light_on(lights.head_lights_pin)
                hl_state = 1
            elif self.lux > threshold and hl_state == 1:
                lights.turn_light_off(lights.head_lights_pin)
                hl_state = 0
            self.update_config_file('Console', 'headlights_state', hl_state)
        nextion.receive_serial_data()
        await asyncio.sleep(30)

    async def run_nextion(self):
        print('run_nextion')

        try:
            nextion = Nextion()
            await asyncio.gather(
                asyncio.to_thread()
            )
            await asyncio.sleep(3)
            await asyncio.gather(
                asyncio.to_thread(nextion.nextion_update(self.data_objects))
            )
        except asyncio.TimeoutError:
            print('Timeout')

def initialize_console():
    console = Console()

    time.sleep(5)
    asyncio.run(console.update_sensors())
    time.sleep(3)
    asyncio.run(console.run_nextion())
    time.sleep(3)

    console.process_command()



def run_console():
    console = Console()

    console.update_config_file('Console', 'state', 'running')
    while True:
        asyncio.run(console.update_sensors())



console = Console()
console.update_config_file('Console', 'state', 'initializing')
asyncio.run(console.update_sensors())
nextion = Nextion()
console = Console()
nextion.nextion_reset()
nextion.nextion_update(console.data_objects)
asyncio.run(console.auto_headlights())
console.process_command()
