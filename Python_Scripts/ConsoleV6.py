import os
import time
from configparser import ConfigParser
import concurrent.futures
import RPi.GPIO as GPIO
import LuxV2 as lux
import EnviroV2 as enviro
import NextionV2 as nextion
import LightsV2 as lights


from concurrent.futures import wait, ALL_COMPLETED, as_completed

config = ConfigParser()
file = ('console_config.ini')
config.read(file)

class Console:

    def __init__(self):
        self.current_lux = float(config.get('Lux', 'lux'))
        self.current_threshold = int(config.get('Console', 'threshold'))

        self.itemp = str(config.get('Environment', 'inside_temp'))
        self.otemp = str(config.get('Environment', 'outside_temp'))
        self.ihumid = str(config.get('Environment', 'inside_humidity'))
        self.ohumid = str(config.get('Environment', 'outside_humidity'))
        self.threshold = str(config.get('Console', 'threshold'))
        self.hl_enabled = str(config.get('Console', 'auto_headlights_enabled'))
        self.headlights = str(config.get('Console', 'auto_headlights'))
        self.hl_pin = 6



        self.data_objects = {'temperature_inside': {'var': self.itemp, 'nextion_field': 'InTemp.txt="'},
                         'temperature_outside': {'var': self.otemp, 'nextion_field': 'OutTemp.txt="'},
                         'humidity_inside': {'var': self.ihumid, 'nextion_field': 'InHumid.txt="'},
                         'humidity_outside': {'var': self.ohumid, 'nextion_field': 'OutHumid.txt="'},
                         'headlights_threshold': {'var': self.threshold, 'nextion_field': 'Settings.thold.val='},
                         'headlights_auto': {'var': self.hl_enabled, 'nextion_field': 'ahenable.val='},
                             'headlights_state': {'var': self.headlights, 'nextion_field': 'headlights.picc='},
                         }

        self.console_commands = {  # 'Auto_Headlights': {'command': self.auto_headlights_mode},
                                'Threshold': {'command': self.update_threshold},
                                'Restart': {'command': self.restart_console},
                                'Shutdown': {'command': self.shutdown_console},
                                }
        self.last_nextion_field_initialized = None

    def read_config(self):
        config.read('console_config.ini')


    def restart_console(self, value):
        # Restart Console Pi
        if value == "True":
            os.system("sudo shutdown -r now")



    def shutdown_console(self, value):
        # Shutdown Console Pi
        if value == "True":
            os.system("sudo shutdown -h now")



    def update_threshold(self, value):
        # Update config with new value from Nextion
        current_threshold = config.get("Console", "threshold")
        if value != current_threshold:
            config["Console"] = {"threshold": str(value)}
            self.config_write()

    def decode_commands(self, prefix, key):
        print('Decoding Command')
        if prefix == 'Lights':
            lights.decode_commands(key)
            return key
        if prefix is 'Console' and key in self.console_commands:
            entry = self.console_commands[key]
            entry['command'](nextion.data_value)


    def update_enviro_data(self, cycles, interval, sleep):
        print('Updating Enviro Data')
        self.current_itempf = enviro.get_inside_temp(cycles, interval)
        self.current_otempf = enviro.get_outside_temp(cycles, interval)
        self.current_ihumid = enviro.get_inside_humidity(cycles, interval)
        self.current_ohumid = enviro.get_outside_humidity(cycles, interval)
        config.set('Environment', 'inside_temp', str(self.current_itempf))
        config.set('Environment', 'outside_temp', str(self.current_otempf))
        config.set('Environment', 'inside_humidity', str(self.current_ihumid))
        config.set('Environment', 'outside_humidity', str(self.current_ohumid))
        self.config_write()
        print('Writing Enviro Data')
        config.read(file)
        self.nextion_update()
        print('Sending Enviro Data')
        time.sleep(sleep)


    def update_lux_data(self, cycles, interval, sleep):
        print('Updating Lux Data')
        self.current_lux = lux.get_lux(cycles, interval)
        config.set('Lux', 'lux', str(self.current_lux))
        self.config_write()
        print("Writing Lux Data")
        config.read(file)
        self.nextion_update()
        time.sleep(sleep)


    def nextion_update(self):
        console = Console()
        for k, v in console.data_objects.items():
            config.read('console_config.ini')
            field = v['nextion_field']
            data = v['var']
            data_m = data + '"'

            if k == 'headlights_threshold':
                print(field, data)
                nextion.write(field, data)  # write data without quotes for int value
            elif k in ['headlights_auto', 'headlights_state']:
                nextion.write(field, data)
            else:
                print(field, data_m)
                nextion.write(field, data_m)  # write data with quotes for txt value
            if field == console.last_nextion_field_initialized:
                continue

    def auto_headlights_check(self):
        self.hl_state = GPIO.input(self.hl_pin)
        print(self.hl_state)
        self.hl_sleep = int(config.get('Lux_Config', 'sleep_timer'))
        while True:
            print('Auto Headlights Check')
            if self.current_lux <= self.current_threshold:
                if self.hl_state == 1:
                    print("Headlights already on")
                    break
                elif self.hl_state == 0:
                    GPIO.output(self.hl_pin, 1)
                    config.set('Console', 'auto_headlights', '1')
                    with open('console_config.ini', 'w') as configfile:
                            config.write(configfile)
                    config.read('console_config.ini')

            elif self.current_lux >= self.current_threshold:
                if self.hl_state == 1:
                    config.set('Console', 'auto_headlights', '4')
                    with open('console_config.ini', 'w') as configfile:
                        config.write(configfile)
                    config.read('console_config.ini')
                elif self.hl_state == 0:
                    GPIO.output(self.hl_pin, 1)
                    config.set('Console', 'auto_headlights', '4')
                    with open('console_config.ini', 'w') as configfile:
                        config.write(configfile)
                    config.read('console_config.ini')

            time.sleep(self.hl_sleep)


    def config_write(self):
        with open('console_config.ini', 'w') as configfile:
            config.write(configfile)
            self.read_config()


config = ConfigParser()
config.read('console_config.ini')


def update_enviro_data(cycles, interval, sleep):
    print('Updating Enviro Data')
    console = Console()
    current_itempf = enviro.get_inside_temp(cycles, interval)
    current_otempf = enviro.get_outside_temp(cycles, interval)
    current_ihumid = enviro.get_inside_humidity(cycles, interval)
    current_ohumid = enviro.get_outside_humidity(cycles, interval)
    config.set('Environment', 'inside_temp', str(current_itempf))
    config.set('Environment', 'outside_temp', str(current_otempf))
    config.set('Environment', 'inside_humidity', str(current_ihumid))
    config.set('Environment', 'outside_humidity', str(current_ohumid))
    console.config_write()
    config.read(file)
    console.nextion_update()
    time.sleep(sleep)


def console_initialize():
    console = Console()
    print('Initializing')
    cycles = int(config.get('Initialize', 'cycles'))
    interval = int(config.get('Initialize', 'interval'))
    sleep = 0
    nextion.nextion_reset()
    console.update_enviro_data(cycles, interval, sleep)
    time.sleep(5)
    console.update_lux_data(cycles, interval, sleep)
    time.sleep(5)
    console_run()




def console_receive():
    #prefix = nextion.data_prefix
    #key = nextion.data_key
    #value = nextion.data_value
    try:
        while True:
            nextion.receive_data()
            print(nextion.command_data)
            prefix = nextion.command_data[0]
            key = nextion.command_data[1]
            console = Console()
            console.decode_commands(prefix, key)
            nextion.command_data = []
    except KeyboardInterrupt:
        print('Quit')


    finally: pass

def console_run():

    cycles = int(config.get('Run', 'cycles'))
    interval = int(config.get('Run', 'interval'))
    sleep = int(config.get('Run', 'sleep_timer'))
    lux_sleep = int(config.get('Lux_Config', 'sleep_timer'))
    try:
        while True:
            print('Running')
            console = Console()
            with concurrent.futures.ThreadPoolExecutor() as console_exec:

                t1 = console_exec.submit(console.auto_headlights_check)
                t2 = console_exec.submit(console_receive)
                t3 = console_exec.submit(update_enviro_data, cycles, interval, sleep)
                t4 = console_exec.submit(console.update_lux_data, cycles, interval, lux_sleep)
                t5 = console_exec.submit(console.auto_headlights_check)

                threads = [t1, t2, t3, t4, t5]
                for t in threads:
                    print(str(t), t.result)
    except KeyboardInterrupt:
        print('Quit')

console_initialize()





