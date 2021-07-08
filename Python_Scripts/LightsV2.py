import RPi.GPIO as GPIO
from configparser import ConfigParser


config = ConfigParser()
config.read('console_config.ini')


def turn_light_on(pin):
    GPIO.output(pin, 1)
    print('light on for pin: ', pin)


def turn_light_off(pin):
    GPIO.output(pin, 0)
    print('light off for pin: ', pin)


lights_commands = {'fl.on': {'pin': 13, 'command': turn_light_on},
               'fl.off': {'pin': 13, 'command': turn_light_off},
               'lb.on': {'pin': 16, 'command': turn_light_on},
               'lb.off': {'pin': 16, 'command': turn_light_off},
               'rl.on': {'pin': 19, 'command': turn_light_on},
               'rl.off': {'pin': 19, 'command': turn_light_off},
               'bl.on': {'pin': 20, 'command': turn_light_on},
               'bl.off': {'pin': 20, 'command': turn_light_off},
               'hl.on': {'pin': 21, 'command': turn_light_on},
               'hl.off': {'pin': 21, 'command': turn_light_off},
               }

last_pin_initialized = None


for k, v in lights_commands.items():
    pin = v['pin']
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)
    if pin == last_pin_initialized:
        continue
    print("GPIO " + str(v['pin']) + " Initialized")
    last_pin_initialized = pin


def decode_commands(key):

    if key in lights_commands:
        # Get the data for the key
        entry = lights_commands[key]
        # Get pin number associated with the key
        pin = entry['pin']
        # Get the command associated with the key and pass the pin number
        entry['command'](pin)
    else:
        print('command not found')