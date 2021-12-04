
import RPi.GPIO as GPIO
import Nextion_v4 as nextion



class Lights:
    def __init__(self):
        self.flood_lights_pin = 13
        self.light_bar_pin = 16
        self.rock_lights_pin = 19
        self.backup_light_pin = 20
        self.head_lights_pin = 26
        self.night_lights_pin = 21
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
                                'nl.on': {'pin': self.night_lights_pin, 'command': self.turn_light_on},
                                'nl.off': {'pin': self.night_lights_pin, 'command': self.turn_light_off},
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
            nextion.Nextion.command_received = ''
        else:
            print('command not found')