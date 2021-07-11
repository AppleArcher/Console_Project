import time
from adafruit_htu21d import HTU21D as HTU21D
import adafruit_tsl2591
import busio
import board
import adafruit_tca9548a
from configparser import ConfigParser

i2c = busio.I2C(board.SCL, board.SDA)
tca = adafruit_tca9548a.TCA9548A(i2c)


class Sensors:

    def __init__(self, location, data_type):
        self.location = location
        self.data_type = data_type
        self.sensor_data = None
        self.data = []
        self.config = ConfigParser()
        self.config_file = 'console_config.ini'
        self.config.read(self.config_file)
        self.cycles = None
        self.interval = None
        self.sensor_dict = {
            'interior_temp_sensor1': {'sensor': HTU21D(tca[2]), 'location': 'interior', 'data_type': 'temperature'},
            'interior_humidity_sensor1': {'sensor': HTU21D(tca[2]), 'location': 'interior', 'data_type': 'humidity'},
            'interior_temp_sensor2': {'sensor': HTU21D(tca[4]), 'location': 'interior', 'data_type': 'temperature'},
            'interior_humidity_sensor2': {'sensor': HTU21D(tca[4]), 'location': 'interior', 'data_type': 'humidity'},
            'exterior_temp_sensor1': {'sensor': HTU21D(tca[3]), 'location': 'exterior', 'data_type': 'temperature'},
            'exterior_humidity_sensor1': {'sensor': HTU21D(tca[3]), 'location': 'exterior', 'data_type': 'humidity'},
            'interior_lux_sensor1': { 'sensor': adafruit_tsl2591.TSL2591(tca[1]), 'location': 'interior', 'data_type': 'lux'},
        }

    def get_console_state(self):
        self.config.read(self.config_file)
        state = self.config['Console']['state']
        if state == 'Initialize':
            self.cycles = int(self.config['Console_Initialize']['cycles'])
            self.interval = int(self.config['Console_Initialize']['interval'])
        elif state == 'Run':
            self.cycles = int(self.config.get('Console_Run', 'cycles'))
            self.interval = int(self.config.get('Console_Run', 'interval'))



    def update_config_file(self, section, location, data_type, data):
        self.config.read(self.config_file)
        self.config[section][location + '_' + data_type] = data
        with open(self.config_file, 'w') as config_file:
            self.config.write(config_file)
            print('Writing data to data_file')
        self.config.read(self.config_file)


# Convert celsius to fahrenheit
def celsius_to_fahrenheit(tc):
    return (((tc * 9) / 5) + 32)

# Average sensor readings taken over time for hysteresis
def average_reading(l):
    return sum(l) / len(l)


class EnvironmentalSensors(Sensors):

    def __init__(self, location, data_type):
        super().__init__(location, data_type)
        self.avg_temp_f = None
        self.temp_f = None
        self.sensor_list = []
        self.data_out = 0

        self.interior_temperature = int
        self.interior_relative_humidity = int
        self.exterior_temperature = int
        self.exterior_relative_humidity = int



    def get_sensor_data(self):
        print('Getting Sensors')
        location = self.location
        data_type = self.data_type
        self.get_console_state()
        sensor_dict = self.sensor_dict
        sensor_list = self.sensor_list
        cycles = self.cycles
        interval = self.interval
        data = self.data
        self.data_out = 0
        sensor_data = 0

        def read_temperature(s_list):
            try:
                s_data = 0
                avg_temp_c = 0
                for _ in range(cycles):
                    for sensor in s_list:
                        temp_reading = sensor.temperature
                        avg_temp_c += temp_reading / (cycles * len(s_list))
                        print('Average Temp',avg_temp_c)
                        #data.append(temp_reading)
                        #avg_temp_c = average_reading(data)
                    s_data = round(celsius_to_fahrenheit(avg_temp_c))
                time.sleep(interval)
            finally:
                time.sleep(5)
                print('S_Data ', s_data)
            return s_data

        def read_humidity(s_list):
            try:
                avg_humidity = None
                s_data = None
                for _ in range(self.cycles):
                    for s in s_list:
                        sensor_humidity = s.relative_humidity
                        data.append(sensor_humidity)
                        avg_humidity = average_reading(data)
                    s_data = round(avg_humidity)
                time.sleep(interval)
            finally:
                time.sleep(5)
            return s_data

        def get_sensor_list(location, d_type):
            print('Getting Sensor List')
            last_sensor_found = str
            for v in sensor_dict.values():
                if v['data_type'] == d_type and v['location'] == location:
                    sensor = v['sensor']
                    sensor_list.append(sensor)
                    print('Sensor List = ', sensor_list)
                    if sensor == last_sensor_found:
                        print('Last Sensor Found')
                        continue
                    last_sensor_found = sensor
            if d_type == 'temperature' and location == 'interior':
                sensor_data = read_temperature(sensor_list)

            elif d_type == 'humidity':
                sensor_data = read_humidity(sensor_list)
            return sensor_data


        #
        self.data_out = get_sensor_list(location, data_type)
        self.update_config_file('Environment', str(location), str(data_type), str(self.data_out))
        return self.data_out


def average_lux(data):
    return sum(data) / len(data)


class LuxSensor(Sensors):
    def __init__(self, location, data_type):
        super().__init__(location, data_type)
        self.config.read(self.config_file)
        self.lux_range_old = int(self.config.get('Lux_Config', 'lux_range_old'))
        self.lux_range_new = int(self.config.get('Lux_Config', 'lux_range_new'))
        self.mapped_lux = None
        self.current_lux = None

    # Map raw reading to new range
    def map_lux_values(self):
        self.mapped_lux = round(((self.read_lux_sensor() - 0) * self.lux_range_new / self.lux_range_old) + 0)
        print('Mapped Lux Value - ', self.mapped_lux)
        return self.mapped_lux

    def read_lux_sensor(self):
        self.lux = round(float(self.lux_sensor.lux))
        print('Sensor Read - Lux = ', self.lux)
        return self.lux

    def lux_sensor_setup(self):
        for v in self.sensor_dict.values():
            if 'lux' in v.values():
                sensor = v['sensor']
                #print('Sensor', sensor)
                sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_100MS
                sensor.gain = adafruit_tsl2591.GAIN_LOW
                self.lux_sensor = sensor
                #print('Lux Sensor - ', self.lux_sensor)
                return self.lux_sensor

    def get_lux(self):
        EnvironmentalSensors.get_console_state(self)
        self.lux_sensor_setup()
        try:
            for _ in range(self.cycles):
                self.data.append(self.map_lux_values())
                print('Data = ', self.data)
                time.sleep(self.interval)
            self.current_lux = round(average_lux(self.data))
        finally:
            if tca.i2c.try_lock():
                tca.i2c.unlock()
            time.sleep(5)
        print('Current Lux Value', self.current_lux)
        return self.current_lux



