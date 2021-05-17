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


class RestBackend:

    def __init__(self):
        self._responses = {}

    def _get(self, _url: str):
        """
        Performs GET for given URL. The result is cached.
        Note: subsequent calls with the same URL will result in only one call!
        :param _url: the url to GET
        :return: response (from requests)
        """
        response = self._responses.get(_url)
        if not response:
            response = requests.get(_url)
            self._responses[_url] = response
        return response

    def _get_json(self, _url: str):
        return self._get(_url).json() if self._get(_url).status_code == 200 else None


class MainPageInfo(RestBackend):

    def __init__(self):
        """
        Initializes the object responsible for querying backend for the information showed on main page
        Note that the instance of this class is created *each time* the main page is displayed
        (consequently, because then the view method is called)
        """
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
        ext = self._get_temp('External')
        chm = self._get_temp('Chiminey')
        roo = self._get_temp('Roof')
        whs = self._get_temp('Weather-Station')
        return ext if ext else chm if chm else roo if roo else whs

    def get_temp_internal(self) -> TemperatureReadingJson:
        return self._get_temp('Office')

    def get_temp_bunker(self) -> TemperatureReadingJson:
        return self._get_temp('Bunker')

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
