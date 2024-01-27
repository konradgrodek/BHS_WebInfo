import requests
from .restconfig import *
from core.bean import *

from django.utils.safestring import mark_safe

rest_configuration = RestConfig()

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
            response.raise_for_status()
            self._responses[cache_key] = response
        return response

    # def _get_json(self, _url: str, params=None):
    #     response = self._get(_url, params)
    #     return response.json() if response.status_code == 200 else None

    def _safe_json_get(self, endpoint: RestEndPoint, params=None):
        try:
            get_response = self._get(endpoint.get_url(), params)
            bean_response = json_to_bean(get_response.json()) \
                if get_response.status_code == 200 \
                else ErrorJsonBean(f'Response code {get_response.status_code}')
        except ValueError as err:
            bean_response = ErrorJsonBean(repr(err))
        except requests.Timeout:
            bean_response = NotAvailableJsonBean()
        except requests.ConnectionError as err:
            bean_response = ErrorJsonBean(f'Connection issue: {str(err)}')
        except requests.HTTPError as err:
            bean_response = ErrorJsonBean(f'HTTP Error: {str(err)}')
        except Exception as exc:
            bean_response = ErrorJsonBean(f'Unknown exception: {str(exc)}')

        return bean_response


class SVGGraph(RestBackend):

    def __init__(self):
        RestBackend.__init__(self)

    @staticmethod
    def _empty_svg():
        return mark_safe(
           f'<svg width="1pt" height="1pt" viewBox="0 0 1 1" xmlns="http://www.w3.org/2000/svg" version="1.1"></svg>'
        )

    def _svg(self, _url: str, params: dict) -> str:
        response = None
        try:
            response = self._get(_url, params)
        finally:
            if response is None or response.status_code != 200:
                return SVGGraph._empty_svg()
        _xml = response.text
        # wipe-away the comments, just leave the plain XML, which can be later pasted into web page
        _xml = _xml[_xml.index('<svg'):] if _xml.find('<svg') > 0 else ''
        return mark_safe(_xml)


class ProgressBar(SVGGraph):

    def __init__(self):
        SVGGraph.__init__(self)

    def get_progress_bar(self, percentage: int, size=None, show_border: bool = False,
                         color: str = None, colormap: str = None) -> str:
        return self._svg(rest_configuration.get_progress_bar_endpoint().get_url(),
                         ProgressBarRESTInterface(progress=percentage,
                                                  size=size,
                                                  show_border=show_border,
                                                  color=color, colormap=colormap).params_for_get())


class TemperatureGraph(SVGGraph):

    def __init__(self):
        SVGGraph.__init__(self)

    def get_temp_daily_graph(self, sensor_location: str, graph_title: str, the_date=None) -> str:
        return self._svg(rest_configuration.get_graph_temperature_endpoint().get_url(),
                         TemperatureGraphRESTInterface(
                             sensor_location=sensor_location,
                             the_date=the_date,
                             graph_title=graph_title,
                             style=TemperatureGraphRESTInterface.STYLE_FILLBETWEEN).params_for_get())


class CesspitGraph(SVGGraph):

    def __init__(self):
        SVGGraph.__init__(self)

    def get_today_usage_graph(self) -> str:
        return self._svg(rest_configuration.get_graph_cesspit_today().get_url(), {})

    def get_last_week_usage_graph(self) -> str:
        return self._svg(
            rest_configuration.get_graph_cesspit_week().get_url(),
            CesspitHistoryRESTInterface(days_in_past=7).params_for_get()
        )

    def get_prediction_graph(self) -> str:
        return self._svg(rest_configuration.get_graph_cesspit_prediction().get_url(), {})


class TemperatureInfo(RestBackend):

    def __init__(self):
        RestBackend.__init__(self)
        self.temperatures = {}

    def _get_temp(self, location: str) -> TemperatureReadingJson:
        _temp = self.temperatures.get(location)
        if not _temp:
            all_temps = self._safe_json_get(rest_configuration.get_current_temperature_endpoint())
            # expected list
            if type(all_temps) == list:
                for t in all_temps:
                    self.temperatures[t.sensor_location] = t
                _temp = self.temperatures.get(location)
            else:  # error reported
                _temp = all_temps
        return _temp if _temp is not None else NotAvailableJsonBean()

    def get_temp_external(self) -> TemperatureReadingJson:
        return self._get_temp(SENSOR_LOC_EXTERNAL)

    def get_temp_chimney(self) -> TemperatureReadingJson:
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
        gar = self.get_temp_garden()
        chm = self.get_temp_chimney()
        roo = self.get_temp_roof()
        return ext if ext else gar if gar else chm if chm else roo

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

    def get_temp(self, _sensor_loc) -> TemperatureReadingJson:
        return self._get_temp(_sensor_loc)


class MainPageInfo(TemperatureInfo):

    def __init__(self):
        """
        Initializes the object responsible for querying backend for the information showed on main page
        Note that the instance of this class is created *each time* the main page is displayed
        (consequently, because then the view method is called)
        """
        TemperatureInfo.__init__(self)

    def get_cesspit_level(self) -> CesspitInterpretedReadingJson:
        return self._safe_json_get(rest_configuration.get_current_cesspit_level_endpoint())

    def get_humidity_in(self) -> ValueTendencyJson:
        return self._safe_json_get(rest_configuration.get_current_humidity_in_endpoint())

    def get_pressure(self) -> ValueTendencyJson:
        return self._safe_json_get(rest_configuration.get_current_pressure_endpoint())

    def get_air_quality(self) -> AirQualityInterpretedReadingJson:
        return self._safe_json_get(rest_configuration.get_current_air_quality_endpoint())

    def get_daylight(self) -> DaylightInterpretedReadingJson:
        return self._safe_json_get(rest_configuration.get_current_daylight_endpoint())

    def get_soil_moisture(self) -> list:
        return self._safe_json_get(rest_configuration.get_current_soil_moisture_endpoint())

    def get_solar_plant(self) -> SolarPlantInterpretedReadingJson:
        return self._safe_json_get(rest_configuration.get_current_solar_plant_endpoint())

    def get_precipitation(self) -> PrecipitationObservationsReadingJson:
        return self._safe_json_get(rest_configuration.get_current_precipitation_endpoint())

    def get_wind(self) -> WindObservationsReadingJson:
        return self._safe_json_get(rest_configuration.get_current_wind_endpoint())

    def get_water_tank(self) -> WaterLevelReadingJson:
        return self._safe_json_get(rest_configuration.get_current_water_tank_endpoint())

    def get_cesspit_prediction(self) -> CesspitPredictionJson:
        return self._safe_json_get(rest_configuration.get_current_cesspit_prediction_endpoint())

    def get_system_status(self) -> SystemStatusJson:
        return self._safe_json_get(rest_configuration.get_system_status_endpoint())

    def get_cesspit_log(self) -> ServiceLogJson:
        return self._safe_json_get(rest_configuration.get_current_cesspit_log_endpoint())


class TemperatureDailyStatistics(RestBackend):

    def __init__(self):
        RestBackend.__init__(self)

    def get_daily_statistics(self, sensor_location: str, the_date: datetime) -> TemperatureDailyStatistics:
        return self._safe_json_get(
            rest_configuration.get_history_temperature_daily_endpoint(),
            params=TemperatureStatisticsRESTInterface(
                sensor_location=sensor_location,
                the_date=the_date).params_for_get())


class CesspitInfo(MainPageInfo):

    def __init__(self):
        """
        Creates new object responsible for delivering information for page with cesspit state.
        In order to not duplicate code, this derives from MainPageInfo
        """
        MainPageInfo.__init__(self)