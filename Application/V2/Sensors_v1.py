import time
import configparser
import adafruit_tca9548a
import adafruit_tsl2591
import board
import busio
from adafruit_sht31d import SHT31D as SHT31D

i2c = busio.I2C(board.SCL, board.SDA)
tca = adafruit_tca9548a.TCA9548A(i2c)


class Sensors:

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = '../V3/console_config.ini'
        self.config.read(self.config_file)
        self.option = str
        self.config_update_data = ()
        #self.config = ConfigParser()
        #self.config_file = 'console_config.ini'
        #self.config.read(self.config_file)
        self.cycles = int()
        self.interval = int()
        self.sensor_dict = {
            'interior_temp_sensor1': {'sensor': SHT31D(tca[3]), 'location': 'interior', 'data_type': 'temperature'},
            'interior_humidity_sensor1': {'sensor': SHT31D(tca[3]), 'location': 'interior', 'data_type': 'humidity'},
            'interior_temp_sensor2': {'sensor': SHT31D(tca[3]), 'location': 'interior', 'data_type': 'temperature'},
            'interior_humidity_sensor2': {'sensor': SHT31D(tca[3]), 'location': 'interior', 'data_type': 'humidity'},
            'exterior_temp_sensor1': {'sensor': SHT31D(tca[2]), 'location': 'exterior', 'data_type': 'temperature'},
            'exterior_humidity_sensor1': {'sensor': SHT31D(tca[2]), 'location': 'exterior', 'data_type': 'humidity'},
            'interior_lux_sensor1': { 'sensor': adafruit_tsl2591.TSL2591(tca[1]), 'location': 'interior', 'data_type': 'lux'},
        }




# Convert celsius to fahrenheit


# Average sensor readings taken over time for hysteresis
def average_reading(l):
    return sum(l) / len(l)


class EnvironmentalSensors(Sensors):
    def __init__(self):
        super().__init__()

        self.location = str
        self.data_type = str
        self.avg_temp_f = float()
        self.temp_f = float()
        self.sensor_list = []
        self.data_out = int()
        self.interior_temperature = int()
        self.interior_relative_humidity = int()
        self.exterior_temperature = int()
        self.exterior_relative_humidity = int()
        self.s_data = int()
        self.avg_temp_c = int()

        self.get_console_state()
        time.sleep(3)

    def get_console_state(self):
        self.config.read(self.config_file)
        state = (self.config['Console']['state'])
        if state == 'initializing':
            self.cycles = int(self.config['Console_Initialize']['cycles'])
            self.interval = int(self.config['Console_Initialize']['interval'])
        elif state == 'running':
            self.cycles = int(self.config.get('Console_Run', 'cycles'))
            self.interval = int(self.config.get('Console_Run', 'interval'))



     
    def get_sensor_data(self, location, data_type):
        #print('Getting Sensors')
        self.location = location
        self.data_type = data_type
        sensor_data = int()
        time.sleep(3)
        sensor_dict = self.sensor_dict
        sensor_list = self.sensor_list
        cycles = self.cycles
        interval = self.interval

        def celsius_to_fahrenheit(tc):
            return (((tc * 9) / 5) + 32)

        def read_temperature(s_list):
            avg_temp_c = int()
            print('Sensors -', s_list)
            try:
                for _ in range(cycles):
                    for sensor in s_list:
                        temp_reading = sensor.temperature
                        print('Temp Reading -', temp_reading)
                        avg_temp_c += temp_reading / (cycles * len(s_list))
                    sensor_data = round(celsius_to_fahrenheit(avg_temp_c))
                time.sleep(interval)
                return sensor_data
            finally:
                time.sleep(.1)

     
        def read_humidity(s_list):
            avg_humidity = float()
            try:
                for _ in range(self.cycles):
                    for s in s_list:
                        sensor_humidity = s.relative_humidity
                        avg_humidity += sensor_humidity / (cycles + len(s_list))
                    sensor_data = round(avg_humidity)
                time.sleep(interval)
                return sensor_data
            finally:
                time.sleep(.1)

     
        def get_sensor_list(location, d_type):
            sensor_data = int()
            #print('Getting Sensor List')
            last_sensor_found = str
            sensor_list = []
            for v in sensor_dict.values():
                if v['data_type'] == d_type and v['location'] == location:
                    sensor = v['sensor']
                    sensor_list.append(sensor)
                    #print('Sensor List = ', sensor_list)
                    if sensor == last_sensor_found:
                        #print('Last Sensor Found')
                        continue
                    last_sensor_found = sensor
            if d_type == 'temperature' and location == 'interior':
                #print('Reading Temperature')
                sensor_data = read_temperature(sensor_list)
                #print('Sensor Data -', sensor_data)
            elif d_type == 'temperature' and location == 'exterior':
                sensor_data = read_temperature(sensor_list)
            elif d_type == 'humidity':
                sensor_data = read_humidity(sensor_list)
                #print('Sensor Data -', sensor_data)

            return sensor_data

        self.data_out = get_sensor_list(location, data_type)
        self.option = (str(str(location) + '_' + str(data_type)))
        #self.config_update_data = ('Environmental Data', str(self.option), str(sensor_data))
        return sensor_data


def average_lux(data):
    return sum(data) / len(data)


class LuxSensor(Sensors):
    def __init__(self):
        super().__init__()
        self.config.read(self.config_file)
        self.lux_range_old = int(self.config.get('Lux_Config', 'lux_range_old'))
        self.lux_range_new = int(self.config.get('Lux_Config', 'lux_range_new'))
        self.mapped_lux = int()
        self.current_lux = int()
        self.lux = int()

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
        self.lux_sensor = self.lux_sensor_setup()
        try:
            for _ in range(self.cycles):
                self.current_lux += self.map_lux_values() / self.cycles
                self.current_lux = round(self.current_lux)
                print('Current Lux Value', self.current_lux)
        finally:
            if tca.i2c.try_lock():
                tca.i2c.unlock()
            time.sleep(5)

        return self.current_lux
 
 
 