from configparser import ConfigParser
import sys


class RestEndPoint:

    def __init__(self, _host: str, _port: str, _path: str):
        self.host = _host
        self.port = _port
        self.path = _path
        if not self.path:
            self.path = ''
        elif not self.path.endswith('/'):
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

    def __init__(self):
        ConfigParser.__init__(self)
        self.read(self.CONFIG_FILE if not sys.gettrace() else self.CONFIG_FILE_DEV)

    def get_current_temperature_endpoint(self) -> RestEndPoint:
        return RestEndPoint(_host=self.get(section=self.SECTION_REST, option=self.OPTION_HOST),
                            _port=self.get(section=self.SECTION_REST, option=self.OPTION_PORT),
                            _path=self.get(section=self.SECTION_REST, option=self.OPTION_CURRENT_TEMP))
