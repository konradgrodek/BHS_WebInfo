from configparser import ConfigParser
import sys


class RestEndPoint:

    def __init__(self, _host: str, _port: str, _path: str):
        self.host = _host
        self.port = _port
        self.path = _path
        if not self.path:
            self.path = ''
        elif not self.path.startswith('/'):
            self.path = '/'+self.path

    def get_url(self):
        if not self.host or not self.port:
            return None

        return f'http://{self.host}:{self.port}{self.path}'


class RestConfig(ConfigParser):

    CONFIG_FILE = '/etc/bhs/web-info/web-info.ini'
    CONFIG_FILE_DEV = './info/test/web-info.ini'

    SECTION_REST = 'REST'

    OPTION_HOST = 'host'
    OPTION_PORT = 'port'
    OPTION_CURRENT_TEMP = 'current-temperature'
    OPTION_CURRENT_CESSPIT = 'current-cesspit-level'
    OPTION_CURRENT_PRESSURE = 'current-pressure'
    OPTION_CURRENT_HUMIDITY_IN = 'current-humidity-in'
    OPTION_CURRENT_AIR_QUALITY = 'current-air-quality'
    OPTION_CURRENT_DAYLIGHT = 'current-daylight'
    OPTION_CURRENT_RAIN = 'current-rain'
    OPTION_CURRENT_SOIL_MOISTURE = 'current-soil-moisture'

    def __init__(self):
        ConfigParser.__init__(self)
        self.read(self.CONFIG_FILE if not sys.gettrace() else self.CONFIG_FILE_DEV)

    def get_current_temperature_endpoint(self) -> RestEndPoint:
        return RestEndPoint(_host=self.get(section=self.SECTION_REST, option=self.OPTION_HOST),
                            _port=self.get(section=self.SECTION_REST, option=self.OPTION_PORT),
                            _path=self.get(section=self.SECTION_REST, option=self.OPTION_CURRENT_TEMP))

    def get_current_pressure_endpoint(self) -> RestEndPoint:
        return RestEndPoint(_host=self.get(section=self.SECTION_REST, option=self.OPTION_HOST),
                            _port=self.get(section=self.SECTION_REST, option=self.OPTION_PORT),
                            _path=self.get(section=self.SECTION_REST, option=self.OPTION_CURRENT_PRESSURE))

    def get_current_humidity_in_endpoint(self) -> RestEndPoint:
        return RestEndPoint(_host=self.get(section=self.SECTION_REST, option=self.OPTION_HOST),
                            _port=self.get(section=self.SECTION_REST, option=self.OPTION_PORT),
                            _path=self.get(section=self.SECTION_REST, option=self.OPTION_CURRENT_HUMIDITY_IN))

    def get_current_air_quality_endpoint(self) -> RestEndPoint:
        return RestEndPoint(_host=self.get(section=self.SECTION_REST, option=self.OPTION_HOST),
                            _port=self.get(section=self.SECTION_REST, option=self.OPTION_PORT),
                            _path=self.get(section=self.SECTION_REST, option=self.OPTION_CURRENT_AIR_QUALITY))

    def get_current_cesspit_level_endpoint(self) -> RestEndPoint:
        return RestEndPoint(_host=self.get(section=self.SECTION_REST, option=self.OPTION_HOST),
                            _port=self.get(section=self.SECTION_REST, option=self.OPTION_PORT),
                            _path=self.get(section=self.SECTION_REST, option=self.OPTION_CURRENT_CESSPIT))

    def get_current_daylight_endpoint(self) -> RestEndPoint:
        return RestEndPoint(_host=self.get(section=self.SECTION_REST, option=self.OPTION_HOST),
                            _port=self.get(section=self.SECTION_REST, option=self.OPTION_PORT),
                            _path=self.get(section=self.SECTION_REST, option=self.OPTION_CURRENT_DAYLIGHT))

    def get_current_rain_endpoint(self) -> RestEndPoint:
        return RestEndPoint(_host=self.get(section=self.SECTION_REST, option=self.OPTION_HOST),
                            _port=self.get(section=self.SECTION_REST, option=self.OPTION_PORT),
                            _path=self.get(section=self.SECTION_REST, option=self.OPTION_CURRENT_RAIN))

    def get_current_soil_moisture(self) -> RestEndPoint:
        return RestEndPoint(_host=self.get(section=self.SECTION_REST, option=self.OPTION_HOST),
                            _port=self.get(section=self.SECTION_REST, option=self.OPTION_PORT),
                            _path=self.get(section=self.SECTION_REST, option=self.OPTION_CURRENT_SOIL_MOISTURE))
