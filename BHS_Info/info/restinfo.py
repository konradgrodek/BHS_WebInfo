import requests
from .restconfig import *
from core.bean import *

rest_configuration = RestConfig()


# class BackendException(Exception):
#
#     def __init__(self, response: HttpResponse):
#         self.http_resonse = response


# class BackendCall:
#
#     def __init__(self, backend_url: str):
#         self.backend_url = backend_url
#         self.response = None
#
#     def call(self) -> int:
#         self.response = requests.get(self.backend_url)
#         return self.response.status_code
#

# sensor locations
SENSOR_LOC_EXTERNAL = 'External'
SENSOR_LOC_BUNKER = 'Bunker'
SENSOR_LOC_OFFICE = 'Office'
SENSOR_LOC_SYSTEM = 'System'
SENSOR_LOC_RPIRED = 'RPiRed'
SENSOR_LOC_ATTIC = 'Attic'
SENSOR_LOC_ROOF = 'Roof'
SENSOR_LOC_CHIMINEY = 'Chiminey'
SENSOR_LOC_WEATHERSTATION = 'Weather-Station'
SENSOR_LOC_RPIVIOLET = 'RPiViolet'
SENSOR_LOC_RPICOPPER = 'RPiCopper'
SENSOR_LOC_GARDEN = 'Garden'
SENSOR_LOC_GRASS = 'Grass'


class RestBackend:

    def __init__(self):
        self._responses = {}

    def _get(self, _url: str, params=None):
        """
        Performs GET for given URL. The result is cached.
        Note: subsequent calls with the same URL will result in only one call!
        :param _url: the url to GET
        :return: response (from requests)
        """
        cache_key = _url + (str(params) if params is not None else '')
        response = self._responses.get(cache_key)
        if not response:
            response = requests.get(_url, params=params)
            self._responses[cache_key] = response
        return response

    def _get_json(self, _url: str):
        return self._get(_url).json() if self._get(_url).status_code == 200 else None

    def _safe_json_get(self, endpoint: str):
        try:
            resp = json_to_bean(endpoint)
        except ValueError as err:
            resp = ErrorJsonBean(repr(err))
        except requests.Timeout:
            resp = NotAvailableJsonBean()
        except requests.ConnectionError as err:
            resp = ErrorJsonBean(repr(err))
        except requests.HTTPError as err:
            resp = ErrorJsonBean(repr(err))

        return resp if type(resp) == list or resp.has_succeeded() else None


class SVGGraph(RestBackend):

    def __init__(self):
        RestBackend.__init__(self)

    def _svg(self, _url: str, params: dict) -> str:
        response = self._get(_url, params)
        response.raise_for_status()
        _xml = response.text
        # wipe-away the comments, just leave the plain XML, which can be later pasted into web page
        return _xml[_xml.index('<svg'):]


class TemperatureGraph(SVGGraph):

    def __init__(self):
        SVGGraph.__init__(self)

    def get_temp_daily_graph(self, sensor_location: str, graph_title: str, the_date=None) -> str:
        return self._svg(rest_configuration.get_graph_temperature().get_url(),
                         TemperatureGraphInterface(
                             sensor_location=sensor_location,
                             the_date=the_date,
                             graph_title=graph_title).params())


class TemperatureInfo(RestBackend):

    def __init__(self):
        RestBackend.__init__(self)
        self.temperatures = {}

    def _get_temp(self, location: str) -> TemperatureReadingJson:
        _temp = self.temperatures.get(location)
        if not _temp:
            all_temps = json_to_bean(self._get_json(rest_configuration.get_current_temperature_endpoint().get_url()))
            # expected list
            if type(all_temps) == list:
                for t in all_temps:
                    self.temperatures[t.sensor_location] = t
            _temp = self.temperatures.get(location)
        return _temp

    def get_temp_external(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_EXTERNAL)

    def get_temp_chiminey(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_CHIMINEY)

    def get_temp_roof(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_ROOF)

    def get_temp_weather_station(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_WEATHERSTATION)

    def get_temp_garden(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_GARDEN)

    def get_temp_grass(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_GRASS)

    def get_temp_external_best_available(self) -> TemperatureReadingJson:
        ext = self.get_temp_external()
        chm = self.get_temp_chiminey()
        roo = self.get_temp_roof()
        whs = self.get_temp_weather_station()
        return ext if ext else chm if chm else roo if roo else whs

    def get_temp_internal(self) -> TemperatureReadingJson:
        return self.get_temp_office()

    def get_temp_office(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_OFFICE)

    def get_temp_bunker(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_BUNKER)

    def get_temp_garage(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_SYSTEM)

    def get_temp_attic(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_ATTIC)

    def get_temp_rpi_red(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_RPIRED)

    def get_temp_rpi_copper(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_RPICOPPER)

    def get_temp_rpi_violet(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_RPIVIOLET)


class MainPageInfo(TemperatureInfo):

    def __init__(self):
        """
        Initializes the object responsible for querying backend for the information showed on main page
        Note that the instance of this class is created *each time* the main page is displayed
        (consequently, because then the view method is called)
        """
        TemperatureInfo.__init__(self)

    def get_cesspit_level(self) -> CesspitInterpretedReadingJson:
        return self._safe_json_get(self._get_json(rest_configuration.get_current_cesspit_level_endpoint().get_url()))

    def get_humidity_in(self) -> ValueTendencyJson:
        return self._safe_json_get(self._get_json(rest_configuration.get_current_humidity_in_endpoint().get_url()))

    def get_pressure(self) -> ValueTendencyJson:
        return self._safe_json_get(self._get_json(rest_configuration.get_current_pressure_endpoint().get_url()))

    def get_air_quality(self) -> AirQualityInterpretedReadingJson:
        return self._safe_json_get(self._get_json(rest_configuration.get_current_air_quality_endpoint().get_url()))

    def get_daylight(self) -> DaylightInterpretedReadingJson:
        return self._safe_json_get(self._get_json(rest_configuration.get_current_daylight_endpoint().get_url()))

    def get_rain(self) -> RainReadingJson:
        return self._safe_json_get(self._get_json(rest_configuration.get_current_rain_endpoint().get_url()))

    def get_soil_moisture(self) -> list:
        return self._safe_json_get(self._get_json(rest_configuration.get_current_soil_moisture().get_url()))
