import time
from configparser import ConfigParser
from adafruit_htu21d import HTU21D
import busio
import board
import adafruit_tca9548a
import concurrent.futures
from concurrent.futures import wait, ALL_COMPLETED





config = ConfigParser()
config.read('console_config.ini')

i2c = busio.I2C(board.SCL, board.SDA)
tca = adafruit_tca9548a.TCA9548A(i2c)

sensor_inside1 = HTU21D(tca[2])
#sensor_inside2 = HTU21D(tca[3])
sensor_outside1 = HTU21D(tca[4])
isensor_1 = sensor_inside1
#isensor_2 = sensor_inside2
osensor_1 = sensor_outside1
inside_sensors = [isensor_1]
outside_sensors = [osensor_1]
#current_itempf = ''
#current_ihumid = ''
#current_otempf = ''
#current_ohumid = ''

def timer_sleep():
    sleep_timer = int(config.get('Run', 'sleep_timer'))
    time.sleep(sleep_timer)
# Read inside temp sensors readings in celsius
def read_itemp_sensors():
    return [s.temperature for s in inside_sensors]

# Read outside temp sensor readings celsius
def read_otemp_sensors():
    return [s.temperature for s in outside_sensors]

# Convert celsius to fahrenheit
def celsius_to_fahrenheit(tempc):
    return round(((tempc * 9) / 5) + 32)

# Average sensor readings taken over time for hysteresis
def average_reading(l):
    return sum(l) / len(l)

# Add inside sensor reading to a list for hysteresis
def get_inside_temp(cycles, interval):
    itempc_list = []
    field = 'inside_temp'
    for _ in range(cycles):
        itempc_list.extend(read_itemp_sensors())
        itempc = average_reading(itempc_list)
        current_itempf = celsius_to_fahrenheit(round(itempc))
    #print('Current Itemp:', current_itempf)
    return current_itempf

# Add outside sensor readings to list for hysteresis
def get_outside_temp(cycles, interval):
    time.sleep(5)
    otempc_list = []
    field = 'outside_temp'
    for _ in range(cycles):
        otempc_list.extend(read_otemp_sensors())
        otempc = average_reading(otempc_list)
        current_otempf = celsius_to_fahrenheit(round(otempc))
    #print('Current Otemp:', current_otempf)
    return current_otempf

# Read humidity data from inside sensors
def read_ihumid_sensors():
    return [s.relative_humidity for s in inside_sensors]

# Read humidity data from outside sensors
def read_ohumid_sensors():
    return [s.relative_humidity for s in outside_sensors]

def get_inside_humidity(cycles, interval):
    time.sleep(7)
    ihumid_list = []
    field = 'inside_humidity'
    for _ in range(cycles):
        ihumid_list.extend(read_ihumid_sensors())
        ihumid = average_reading(ihumid_list)
        current_ihumid = int(ihumid)
    #print('Current ihumid: ', current_ihumid)
    return current_ihumid


def get_outside_humidity(cycles, interval):
    time.sleep(8)
    ohumid_list = []
    field = 'outside_humidity'
    for _ in range(cycles):
        ohumid_list.extend(read_ohumid_sensors())
        ohumid = average_reading(ohumid_list)
        current_ohumid = int(ohumid)
    #print('Current ohumid:', current_ohumid)
    return current_ohumid

# noinspection PyTypeChecker
def write_data(field, data):
    #print('Writing Enviromental Data')
   # print('Writing', field, ': ', data)
    config.set('Environment', str(field), str(data))
    with open('console_config.ini', 'w') as configfile:
        config.write(configfile)
        config.read('console_config.ini')
        #print("Environmental Data Written")



def read_sensors(cycles, interval):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        print('Reading Environmental Sensors')
        p1 = executor.submit(get_inside_temp, cycles, interval)
        p2 = executor.submit(get_outside_temp, cycles, interval)
        p3 = executor.submit(get_inside_humidity, cycles, interval)
        p4 = executor.submit(get_outside_humidity, cycles, interval)

        threads = [p1, p2, p3, p4]

        for t in threads:
            config.read('console_config.ini')
            wait(threads, return_when=ALL_COMPLETED)


def enviro_run():
    cycles = int(config.get('Run', 'cycles'))
    interval = int(config.get('Run', 'interval'))
    try:
        while True:
            with concurrent.futures.ThreadPoolExecutor() as thread_exec:
                t1 = thread_exec.submit(get_inside_temp, cycles, interval)
                t2 = thread_exec.submit(get_outside_temp, cycles, interval)
                t3 = thread_exec.submit(get_inside_humidity, cycles, interval)
                t4 = thread_exec.submit(get_outside_humidity, cycles, interval)
                threads = [t1, t2, t3, t4]
                for future in concurrent.futures.as_completed(threads):
                    config.read('console_config.ini')
                    print(future.result())
                timer_sleep()
    except KeyboardInterrupt:
        print('Quit')

