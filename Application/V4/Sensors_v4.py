import time
from configparser import RawConfigParser
import busio
import board
import adafruit_tca9548a
from adafruit_sht31d import SHT31D as SHT31D
import adafruit_tsl2591
import asyncio

i2c = busio.I2C(board.SCL, board.SDA)
tca = adafruit_tca9548a.TCA9548A(i2c)


class Sensor:


    def __init__(self):
        self.config = RawConfigParser()
        self.config_file = "/home/pi/Console/console_config_v4.ini"
        self.config.read(self.config_file)
        self.location = str()
        self.data_type = str()
        self.cycles = 0
        self.interval = 0
        self.temperature_data = 0
        self.humidity_data = 0
        self.average_temperature = int()
        self.average_humidity = int()
        self.data = []
        self.lux_data = 0
        self.sensor_list = []
        self.sensor_dict = {
            'interior_temp_sensor1': {'sensor': SHT31D(tca[2]), 'location': 'interior', 'data_type': 'temperature'},
            'interior_humidity_sensor1': {'sensor': SHT31D(tca[2]), 'location': 'interior', 'data_type': 'humidity'},
            'interior_temp_sensor2': {'sensor': SHT31D(tca[3]), 'location': 'interior', 'data_type': 'temperature'},
            'interior_humidity_sensor2': {'sensor': SHT31D(tca[3]), 'location': 'interior', 'data_type': 'humidity'},
            'exterior_temp_sensor1': {'sensor': SHT31D(tca[4]), 'location': 'exterior', 'data_type': 'temperature'},
            'exterior_humidity_sensor1': {'sensor': SHT31D(tca[4]), 'location': 'exterior', 'data_type': 'humidity'},
            #'exterior_temp_sensor2': {'sensor': SHT31D(tca[5]), 'location': 'exterior', 'data_type': 'temperature'},
            #'exterior_humidity_sensor2': {'sensor': SHT31D(tca[5]), 'location': 'exterior', 'data_type': 'humidity'},
            'interior_lux_sensor1': {'sensor': adafruit_tsl2591.TSL2591(tca[1]), 'location': 'interior', 'data_type': 'lux'},
        }

        self.get_console_state()
        time.sleep(1)

    def get_console_state(self):
        state = self.config['Console']['state']
        if state == 'initializing':
            self.cycles = self.config.getint('Console_Initialize', 'cycles')
            self.interval = self.config.getint('Console_Initialize', 'interval')
        elif state == 'running':
            self.cycles = int(self.config.get('Console_Run', 'cycles'))
            self.interval = int(self.config.get('Console_Run', 'interval'))

    def build_sensor_list(self):
        self.sensor_list = []
        last_sensor_found = str
        for v in self.sensor_dict.values():
            if v['data_type'] == self.data_type and v['location'] == self.location:
                sensor = v['sensor']
                self.sensor_list.append(sensor)
                if sensor == last_sensor_found:
                    continue
                last_sensor_found = sensor
        return self.sensor_list

    #def build_sensor_list2(self):


def celsius_to_fahrenheit(tc):
    return ((tc * 9) / 5) + 32


class Temperature(Sensor):

    async def read_sensor_temperature(self):
        self.average_temperature = 0
        readings = []
        for s in self.sensor_list:
            for _ in range(self.cycles):
                reading = s.temperature
                readings.append(reading)
                print(readings)
                await asyncio.sleep(self.interval)
        #readings = [s.temperature for s in self.sensor_list for _ in range(self.cycles)]
        for temps in readings:
            self.average_temperature += round((celsius_to_fahrenheit(temps)) / ((self.cycles) * len(self.sensor_list)))
        return self.average_temperature

    def get_temperature(self, location):
        self.location = location
        self.data_type = 'temperature'
        self.build_sensor_list()
        self.temperature_data = asyncio.run(self.read_sensor_temperature())
        self.data = (self.location, self.data_type, str(self.temperature_data))
        return self.data


class Humidity(Sensor):

    async def read_sensor_humidity(self):
        self.average_humidity = 0
        readings = []
        for s in self.sensor_list:
            for _ in range(self.cycles):
                reading = s.relative_humidity
                readings.append(reading)
                print(readings)
                await asyncio.sleep(self.interval)
        #readings = [s.temperature for s in self.sensor_list for _ in range(self.cycles)]
        for humids in readings:
            self.average_humidity += round(humids / ((self.cycles) * len(self.sensor_list)))
        return self.average_humidity

    def get_humidity(self, location):
        self.location = location
        self.data_type = 'humidity'
        self.get_console_state()
        self.build_sensor_list()
        self.humidity_data = asyncio.run(self.read_sensor_humidity())
        self.data = (self.location, self.data_type, str(self.humidity_data))
        return self.data


class Lux(Sensor):
        def __init__(self):
            super().__init__()
            self.lux_range_old = int(self.config.get('Lux_Config', 'lux_range_old'))
            self.lux_range_new = int(self.config.get('Lux_Config', 'lux_range_new'))
            self.mapped_lux = int()


        def average_lux(data):
            return sum(data) / len(data)

        # Map raw reading to new range
        def map_lux_values(self):
            self.mapped_lux = round(((self.read_lux_sensor() - 0) * self.lux_range_new / self.lux_range_old) + 0)
            print('Mapped Lux = ', self.mapped_lux)
            return self.mapped_lux

        def read_lux_sensor(self):
            self.lux = round(float(self.lux_sensor.lux))
            #print('Sensor Read - Lux = ', self.lux)
            return self.lux

        def lux_sensor_setup(self):
            for v in self.sensor_dict.values():
                if 'lux' in v.values():
                    sensor = v['sensor']
                    # print('Sensor', sensor)
                    sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_100MS
                    sensor.gain = adafruit_tsl2591.GAIN_LOW
                    self.lux_sensor = sensor
                    # print('Lux Sensor - ', self.lux_sensor)
                    return self.lux_sensor

        def get_lux(self):
            self.lux_sensor_setup()
            self.lux_data = 0
            try:
                for _ in range(self.cycles):
                    self.lux_data += self.map_lux_values() / self.cycles
                    self.lux_data = round(self.lux_data)
                    print('Current Lux Value', self.lux_data)
            finally:
                if tca.i2c.try_lock():
                    tca.i2c.unlock()
                time.sleep(5)

            return self.lux_data








