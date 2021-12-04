import time
from configparser import ConfigParser

import adafruit_tca9548a
import adafruit_tsl2591
import board
import busio

config = ConfigParser()
config.read('console_config.ini')

i2c = busio.I2C(board.SCL, board.SDA)
tca = adafruit_tca9548a.TCA9548A(i2c)



sensor = adafruit_tsl2591.TSL2591(tca[1])
sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_100MS
sensor.gain = adafruit_tsl2591.GAIN_LOW
lux_sensor = sensor
config.read('console_config.ini')
m_lux = 0
current_lux = ''

s
    lux = round(float(lux_sensor.lux))
    return lux

# Map raw reading to new range
def lux_map():
    lux_range_old = int(config.get('Lux_Config', 'lux_range_old'))
    lux_range_new = int(config.get('Lux_Config', 'lux_range_new'))
    m_lux = round(((read_sensor() - 0) * lux_range_new / lux_range_old) + 0)
    return m_lux

# Average lux_list
def average_lux(l):
    return sum(l) / len(l)

# Create lux reading list for hysteresis
def get_lux(cycles, interval):
    lux_list = []
    while True:
        for _ in range(cycles):
            lux_list.append(lux_map())
            time.sleep(interval)
        current_lux = round(average_lux(lux_list))
        print("Current Lux: ", current_lux)
        config_write_lux(current_lux)
        return current_lux

def config_write_lux(lux):
    config.set('Lux', 'lux', str(lux))
    with open('console_config.ini', 'w') as configfile:
        config.write(configfile)

def lux_run():
    timer_sleep = int(config.get('Lux_Config', 'sleep_timer'))
    cycles = int(config.get('Run', 'cycles'))
    interval = int(config.get('Run', 'interval'))
    try:
        while True:
            get_lux(cycles, interval)
            time.sleep(timer_sleep)

    except KeyboardInterrupt:
        print('Quit')

