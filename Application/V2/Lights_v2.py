from configparser import ConfigParser

import RPi.GPIO as GPIO

config = ConfigParser()
config.read('console_config.ini')


class Lights:
    def __init__(self):
        #super().__init__()
        self.flood_lights_pin = 13
        self.light_bar_pin = 16
        self.rock_lights_pin = 19
        self.backup_light_pin = 20
        self.head_lights_pin = 21
        self.lights_commands = {'fl.on': {'pin': self.flood_lights_pin, 'command': self.turn_light_on},
                                'fl.off': {'pin': self.flood_lights_pin, 'command': self.turn_light_off},
                                'lb.on': {'pin': self.light_bar_pin, 'command': self.turn_light_on},
                                'lb.off': {'pin': self.light_bar_pin, 'command': self.turn_light_off},
                                'rl.on': {'pin': self.rock_lights_pin, 'command': self.turn_light_on},
                                'rl.off': {'pin': self.rock_lights_pin, 'command': self.turn_light_off},
                                'bl.on': {'pin': self.backup_light_pin, 'command': self.turn_light_on},
                                'bl.off': {'pin': self.backup_light_pin, 'command': self.turn_light_off},
                                'hl.on': {'pin': self.head_lights_pin, 'command': self.turn_light_on},
                                'hl.off': {'pin': self.head_lights_pin, 'command': self.turn_light_off},
                                }

        last_pin_initialized = None

        for k, v in self.lights_commands.items():
            pin = v['pin']
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)
            if pin == last_pin_initialized:
                continue
            print("GPIO " + str(v['pin']) + " Initialized")
            last_pin_initialized = pin




    def turn_light_on(self, pin):
        GPIO.output(pin, 1)
        print('light on for pin: ', pin)

    def turn_light_off(self, pin):
        GPIO.output(pin, 0)
        print('light off for pin: ', pin)

    def decode_command(self, data):
        if data in self.lights_commands:
            # Get the data for the key
            entry = self.lights_commands[data]
            # Get pin number associated with the key
            pin = entry['pin']
            # Get the command associated with the key and pass the pin number
            entry['command'](pin)
        else:
            print('command not found')

#lights = Lights()
#lights.decode_command('fl.on')
#lights.decode_command('fl_off')
#lights.decode_command('lb.on')
#lights.decode_command('lb_off')
#lights.decode_command('rl.on')
#lights.decode_command('rl_off')
#lights.decode_command('bl.on')
#lights.decode_command('bl_off')
#lights.decode_command('hl.on')
#lights.decode_command('hl_off')