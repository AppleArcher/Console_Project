from configparser import RawConfigParser
import time
from Application.V4.Sensors_v4 import Temperature, Humidity


# noinspection PyMethodMayBeStatic,PyUnusedLocal,SpellCheckingInspection
class Console:

    def __init__(self):
        self.config = RawConfigParser()
        self.config_file = '/home/pi/Console/config.ini'
        self.config.read(self.config_file)
        self.config_data = str
        self.auto_headlights_mode = int()
        self.console_state = self.config['Console']['state']
        self.received_command = ''
        self.received_value = ''
        self.headlights_state = self.config.get('Console', 'threshold_setting')
        self.interior_temperature = []
        self.exterior_temperature = []
        self.interior_humidity = []
        self.exterior_humidity = []
        self.args = []
        self.current_lux = 0
        self.current_auto_headlights_lux_threshold = self.config['Console']['threshold_setting']
# Dictionary to map data to the appropriate Nextion field and type for update
        self.nextion_data_map = {'interior_temperature': {'config_data': self.config['Environmental_Data']['interior_temperature'], 'nextion_field': 'InTemp.txt="', 'type': 'txt'},
                                 'exterior_temperature': {'config_data': self.config['Environmental_Data']['exterior_temperature'], 'nextion_field': 'OutTemp.txt="', 'type': 'txt'},
                                 'interior_humidity': {'config_data': self.config['Environmental_Data']['interior_humidity'], 'nextion_field': 'InHumid.txt="', 'type': 'txt'},
                                 'exterior_humidity': {'config_data': self.config['Environmental_Data']['exterior_humidity'], 'nextion_field': 'OutHumid.txt="', 'type': 'txt'},
                                 'headlights_threshold': {'config_data': self.config['Console']['threshold_setting'], 'nextion_field': 'Settings.thold.val=', 'type': 'int'},
                                 'headlights_auto': {'config_data': self.config['Console']['auto_headlights_mode'],'nextion_field': 'ahenable.val=', 'type': 'int'},
                                 'headlights_state': {'config_data': self.config.get('Console', 'headlights_state'),'nextion_field': 'headlights.picc=', 'type': 'int'},
                                 }
        self.last_nextion_field_initialized = None

    def update_config_file(self, data):
        section = data[0]
        option = data[1] + '_' + data[2]
        value = data[3]
        self.config[section][option] = value
        with open(self.config_file, 'w') as config_file:
            self.config.write(config_file)
            time.sleep(5)
            config_file.close()
            self.config.read(self.config_file)


    def get_enviro_data(self):
        section = 'Environmental_Data'
        n = 0
        while n == 0:
            t = Temperature()
            h = Humidity()
            print('Enviro')                                             # Debugging
            self.interior_temperature = t.get_temperature('interior')
            self.exterior_temperature = t.get_temperature('exterior')
            self.interior_humidity = h.get_humidity('interior')
            self.exterior_humidity = h.get_humidity('exterior')
            data = [self.interior_temperature, self.exterior_temperature,
                    self.interior_humidity, self.exterior_humidity]
            for i in data:
                self.args = section, i[0], i[1], i[2]
                self.args = tuple(self.args)

                self.update_config_file(self.args)
                print(i)                                                # Debugging
                time.sleep(2)
#            self.config.read(self.config_file)
            state = self.config['Console']['state']
            if state == 'initializing':
                n = 1
                break
            elif state == 'running':
                time.sleep(5)

console = Console()
console.get_enviro_data()