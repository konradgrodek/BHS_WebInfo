from django.http import HttpResponse, HttpResponseBadRequest
from django.template import loader

from datetime import timedelta

import logging as log

from .restinfo import *

UNKNOWN = '?'
CELSIUS = '\u2103'
REQUEST_DATE_FORMAT = '%Y-%m-%d'


def index(request):
    template = loader.get_template('index.html')

    information = MainPageInfo()

    # note: by convention, the rest-client do not raise any deliberated exceptions
    # if any sort of an error occurs, the client returns empty objects (None)
    # it is up to front-end to handle unknown information
    temp_internal = information.get_temp_internal()
    temp_external = information.get_temp_external_best_available()
    temp_bunker = information.get_temp_bunker()
    cesspit = information.get_cesspit_level()
    humidity_in = information.get_humidity_in()
    air_quality = information.get_air_quality()
    pressure = information.get_pressure()
    daylight = information.get_daylight()
    solar_plant = information.get_solar_plant()
    precipitation = information.get_precipitation()
    wind = information.get_wind()
    progress_bars = ProgressBar()

    _current_date = datetime.today().strftime('%Y-%m-%d %H:%M')

    _tendency_icons = {
        Tendency.RISING: 'arrow-up-right.svg',
        Tendency.STEADY: 'arrow-right.svg',
        Tendency.FALLING: 'arrow-down-right.svg'
    }

    _cesspit_states = {
        CesspitState.OK: 'bg-success',
        CesspitState.WARNING: 'bg-warning',
        CesspitState.CRITICAL: 'bg-danger'
    }

    str_temp_external = f'{temp_external.temperature:.1f} {CELSIUS}' if temp_external else UNKNOWN
    str_temp_internal = f'{temp_internal.temperature:.1f} {CELSIUS}' if temp_internal else UNKNOWN
    str_temp_bunker = f'{temp_bunker.temperature:.1f} {CELSIUS}' if temp_bunker else UNKNOWN
    tm_temp_external = temp_external.timestamp.strftime('%H:%M') if temp_external else ''
    tm_temp_internal = temp_internal.timestamp.strftime('%H:%M') if temp_internal else ''
    tm_temp_bunker = temp_bunker.timestamp.strftime('%H:%M') if temp_bunker else ''

    str_humidity_in = f'{humidity_in.current_value:.0f}' if humidity_in else UNKNOWN
    tenicon_hum_in = _tendency_icons[humidity_in.tendency if humidity_in else Tendency.STEADY]

    str_pressure = f'{pressure.current_value:.0f}' if pressure else UNKNOWN
    tenicon_pressure = _tendency_icons[pressure.tendency if pressure else Tendency.STEADY]

    cesspit_state = _cesspit_states[cesspit.state] if cesspit else ''
    cesspit_level_label = f'{cesspit.original_reading.fill:.2f}' if cesspit else UNKNOWN
    cesspit_level = str(int(cesspit.original_reading.fill)) if cesspit else '0'
    cesspit_reading_state = '' if not cesspit else 'KO' if cesspit.failure_detected else 'OK'
    tm_cesspit = cesspit.original_reading.timestamp.strftime('%H:%M') if cesspit else ''

    aq_pm_10_label = air_quality.pm_10 if air_quality else UNKNOWN
    aq_pm_10_level = 0 if not air_quality else air_quality.pm_10 if air_quality.pm_10 <= 100 else 100
    aq_pm_10_color = '' if not air_quality \
        else 'bg-success' if air_quality.pm_10 < 100 \
        else 'bg-warning' if air_quality.pm_10 < 200 \
        else 'bg-danger'

    aq_pm_2_5_label = air_quality.pm_2_5 if air_quality else UNKNOWN
    aq_pm_2_5_level = 0 if not air_quality else air_quality.pm_2_5 if air_quality.pm_2_5 <= 100 else 100
    aq_pm_2_5_color = '' if not air_quality \
        else 'bg-success' if air_quality.pm_2_5 < 100 \
        else 'bg-warning' if air_quality.pm_2_5 < 200 \
        else 'bg-danger'

    tm_aq = air_quality.original_reading.timestamp.strftime('%H:%M') if air_quality else ''

    if precipitation.has_succeeded() and precipitation.is_raining:
        sky_state_icon = 'cloud-rain.svg'  # heavy?
    elif daylight.time_of_day == TimeOfDay.NIGHT:
        sky_state_icon = 'moon.svg'
    elif daylight.original_reading.is_sunlight:
        sky_state_icon = 'sun.svg'
    elif daylight.time_of_day == TimeOfDay.MORNING:
        sky_state_icon = 'sunrise.svg'
    elif daylight.time_of_day == TimeOfDay.EVENING:
        sky_state_icon = 'sunset.svg'
    else:
        sky_state_icon = 'clouds.svg'  # cloud-sun?

    soil_hums = information.get_soil_moisture()
    tenicons_shum = [_tendency_icons[soil_hum.tendency if soil_hum else Tendency.STEADY] for soil_hum in soil_hums]
    strs_shum = [f'{soil_hum.current_value:.1f}' for soil_hum in soil_hums]

    tm_sol = solar_plant.reading.last_production_at.strftime('%Y-%m-%d %H:%M') if solar_plant else UNKNOWN
    sol_prod_now_w = str(solar_plant.reading.current_production_w) if solar_plant else UNKNOWN
    sol_prod_now_perc = str(solar_plant.current_production_perc) if solar_plant else '0'
    sol_prod_now_progress_bar = progress_bars.get_progress_bar(
        percentage=solar_plant.current_production_perc, size=(4, 0.32), show_border=True)
    sol_prod_today = f'{solar_plant.reading.daily_production_kwh:.1f}' if solar_plant else UNKNOWN
    sol_prod_h_min_w = str(solar_plant.reading.hourly_min_w) if solar_plant else UNKNOWN
    sol_prod_h_min_perc = str(solar_plant.hourly_min_perc) if solar_plant else '0'
    sol_prod_h_avg_w = str(solar_plant.reading.hourly_avg_w) if solar_plant else UNKNOWN
    sol_prod_h_avg_perc = str(solar_plant.hourly_avg_perc) if solar_plant else '0'
    sol_prod_h_max_w = str(solar_plant.reading.hourly_max_w) if solar_plant else UNKNOWN
    sol_prod_h_max_perc = str(solar_plant.hourly_max_perc) if solar_plant else '0'

    # wind direction
    _wind_direction_icons = {
        WindDirection.S: 'arrow-up-circle.svg',
        WindDirection.SW: 'arrow-up-right-circle.svg',
        WindDirection.W: 'arrow-right-circle.svg',
        WindDirection.NW: 'arrow-down-right-circle.svg',
        WindDirection.N: 'arrow-down-circle.svg',
        WindDirection.NE: 'arrow-down-left-circle.svg',
        WindDirection.E: 'arrow-left-circle.svg',
        WindDirection.SE: 'arrow-up-left-circle.svg',
        WindDirection.UNKNOWN: 'circle.svg'
    }
    # take direction and peak from long-term observations, current speed from short-term
    wind_dir = wind.long_term_observation.direction if wind.has_succeeded() else WindDirection.UNKNOWN
    wind_dir_icon = _wind_direction_icons[wind_dir]
    # wind_dir_var = f'{int(wind.long_term_observation.direction_var)}%' if wind.has_succeeded() else UNKNOWN
    wind_peak = f'{int(wind.long_term_observation.wind_peak)} km/h' if wind.has_succeeded() else UNKNOWN
    wind_speed = f'{int(wind.short_term_observation.wind_speed)} km/h' if wind.has_succeeded() else UNKNOWN
    # wind_speed_var = f'{int(wind.short_term_observation.wind_variance)}%' if wind.has_succeeded() else UNKNOWN

    # precipitation
    rain_mm = f'{precipitation.precipitation_mm:.1f} mm' if precipitation.has_succeeded() else UNKNOWN
    rain_obs_h = f'{precipitation.observation_duration_h} h' if precipitation.has_succeeded() else UNKNOWN

    context = {
        'temp_external': str_temp_external,
        'temp_internal': str_temp_internal,
        'temp_bunker': str_temp_bunker,
        'tm_temp_external': tm_temp_external,
        'tm_temp_internal': tm_temp_internal,
        'tm_temp_bunker': tm_temp_bunker,
        'humidity_in': str_humidity_in,
        'hum_in_tendency_icon': tenicon_hum_in,
        'pressure': str_pressure,
        'pressure_tendency_icon': tenicon_pressure,
        'cesspit_state': cesspit_state,
        'cesspit_level_label': cesspit_level_label,
        'cesspit_level': cesspit_level,
        'cesspit_reading_state': cesspit_reading_state,
        'tm_cesspit': tm_cesspit,
        'aq_pm_10_label': aq_pm_10_label,
        'aq_pm_10_level': aq_pm_10_level,
        'aq_pm_10_color': aq_pm_10_color,
        'aq_pm_2_5_label': aq_pm_2_5_label,
        'aq_pm_2_5_level': aq_pm_2_5_level,
        'aq_pm_2_5_color': aq_pm_2_5_color,
        'tm_aq': tm_aq,
        'sunrise': daylight.sunrise,
        'sunset': daylight.sunset,
        'sky_state_icon': sky_state_icon,
        'daylight_perc': daylight.original_reading.luminescence_perc,
        'soil_hum_tendency_icon_0': tenicons_shum[0],
        'soil_hum_0': strs_shum[0],
        'soil_hum_tendency_icon_1': tenicons_shum[1],
        'soil_hum_1': strs_shum[1],
        'soil_hum_tendency_icon_2': tenicons_shum[2],
        'soil_hum_2': strs_shum[2],
        'tm_sol': tm_sol,
        'sol_prod_now_w': sol_prod_now_w,
        'sol_prod_now_perc': sol_prod_now_perc,
        'sol_prod_now_progress': sol_prod_now_progress_bar,
        'sol_prod_today': sol_prod_today,
        'sol_prod_h_min_w': sol_prod_h_min_w,
        'sol_prod_h_min_perc': sol_prod_h_min_perc,
        'sol_prod_h_avg_w': sol_prod_h_avg_w,
        'sol_prod_h_avg_perc': sol_prod_h_avg_perc,
        'sol_prod_h_max_w': sol_prod_h_max_w,
        'sol_prod_h_max_perc': sol_prod_h_max_perc,
        'wind_dir': wind_dir.name,
        'wind_dir_icon': wind_dir_icon,
        'wind_speed': wind_speed,
        'wind_peak': wind_peak,
        'rain_mm': rain_mm,
        'rain_obs_h': rain_obs_h,
        'date': _current_date
    }

    return HttpResponse(template.render(context, request))


def external_temperature(request):
    template = loader.get_template('temperatures_ext.html')

    information = TemperatureInfo()
    graph = TemperatureGraph()

    _current_date = datetime.today().strftime('%Y-%m-%d %H:%M')

    temp_external = information.get_temp_external()
    temp_chimney = information.get_temp_chimney()
    temp_roof = information.get_temp_roof()
    temp_garden = information.get_temp_garden()
    temp_grass = information.get_temp_grass()

    str_temp_external = f'{temp_external.temperature:.1f} {CELSIUS}' if temp_external else UNKNOWN
    tm_temp_external = temp_external.timestamp.strftime('%H:%M') if temp_external else ''
    str_temp_chimney = f'{temp_chimney.temperature:.1f} {CELSIUS}' if temp_chimney else UNKNOWN
    tm_temp_chimney = temp_chimney.timestamp.strftime('%H:%M') if temp_chimney else ''
    str_temp_roof = f'{temp_roof.temperature:.1f} {CELSIUS}' if temp_roof else UNKNOWN
    tm_temp_roof = temp_roof.timestamp.strftime('%H:%M') if temp_roof else ''
    str_temp_garden = f'{temp_garden.temperature:.1f} {CELSIUS}' if temp_garden else UNKNOWN
    tm_temp_garden = temp_garden.timestamp.strftime('%H:%M') if temp_garden else ''
    str_temp_grass = f'{temp_grass.temperature:.1f} {CELSIUS}' if temp_grass else UNKNOWN
    tm_temp_grass = temp_grass.timestamp.strftime('%H:%M') if temp_grass else ''

    temp_external_graph_svg = mark_safe(
        graph.get_temp_daily_graph(sensor_location=SENSOR_LOC_EXTERNAL,
                                   graph_title='Temperatura zewnętrzna - czujnik pieca'))

    context = {
        'temp_external': str_temp_external,
        'tm_temp_external': tm_temp_external,
        'temp_chimney': str_temp_chimney,
        'tm_temp_chimney': tm_temp_chimney,
        'temp_roof': str_temp_roof,
        'tm_temp_roof': tm_temp_roof,
        'temp_garden': str_temp_garden,
        'tm_temp_garden': tm_temp_garden,
        'temp_grass': str_temp_grass,
        'tm_temp_grass': tm_temp_grass,
        'temp_external_graph': temp_external_graph_svg,
        'date': _current_date
    }

    return HttpResponse(template.render(context, request))


def internal_temperature(request):
    template = loader.get_template('temperatures_int.html')

    information = TemperatureInfo()
    graph = TemperatureGraph()

    _current_date = datetime.today().strftime('%Y-%m-%d %H:%M')

    temp_office = information.get_temp_office()
    temp_attic = information.get_temp_attic()
    temp_bunker = information.get_temp_bunker()
    temp_garage = information.get_temp_garage()

    str_temp_office = f'{temp_office.temperature:.1f} {CELSIUS}' if temp_office else UNKNOWN
    tm_temp_office = temp_office.timestamp.strftime('%H:%M') if temp_office else ''
    str_temp_attic = f'{temp_attic.temperature:.1f} {CELSIUS}' if temp_attic else UNKNOWN
    tm_temp_attic = temp_attic.timestamp.strftime('%H:%M') if temp_attic else ''
    str_temp_bunker = f'{temp_bunker.temperature:.1f} {CELSIUS}' if temp_bunker else UNKNOWN
    tm_temp_bunker = temp_bunker.timestamp.strftime('%H:%M') if temp_bunker else ''
    str_temp_garage = f'{temp_garage.temperature:.1f} {CELSIUS}' if temp_garage else UNKNOWN
    tm_temp_garage = temp_garage.timestamp.strftime('%H:%M') if temp_garage else ''

    temp_office_graph_svg = mark_safe(graph.get_temp_daily_graph(sensor_location=SENSOR_LOC_OFFICE,
                                                                 graph_title='Temperatura w biurze'))

    context = {
        'temp_office': str_temp_office,
        'tm_temp_office': tm_temp_office,
        'temp_attic': str_temp_attic,
        'tm_temp_attic': tm_temp_attic,
        'temp_bunker': str_temp_bunker,
        'tm_temp_bunker': tm_temp_bunker,
        'temp_garage': str_temp_garage,
        'tm_temp_garage': tm_temp_garage,
        'temp_office_graph': temp_office_graph_svg,
        'date': _current_date
    }

    return HttpResponse(template.render(context, request))


# def any_temperature(request):
#     sensor_loc = request.GET.get('sensor')
#     sensor_name = request.GET.get('name')
#     req_date = request.GET.get('date')
#
#     if not sensor_loc:
#         return HttpResponseBadRequest()
#
#     if not sensor_name:
#         sensor_name = UNKNOWN
#
#     _date = datetime.today()
#     if req_date:
#         _date = datetime.strptime(req_date, REQUEST_DATE_FORMAT)
#
#     _is_today = (_date - datetime.today()).days < 1
#
#     _date_minus = _date - timedelta(days=1)
#     _date_plus = _date + timedelta(days=1)
#
#     _str_date = _date.strftime(REQUEST_DATE_FORMAT)
#     _str_date_minus = _date_minus.strftime(REQUEST_DATE_FORMAT)
#     _str_date_plus = _date_plus.strftime(REQUEST_DATE_FORMAT)
#
#     template = loader.get_template('temperature.html')
#
#     information = TemperatureInfo()
#     graph = TemperatureGraph()
#
#     context = {
#         'sensor_name': sensor_name,
#         'temp_current': information.get_,
#         'tm_temp_current': tm_temp_current,
#         'temp_min': temp_min,
#         'tm_temp_min': tm_temp_min,
#         'temp_max': temp_max,
#         'tm_temp_max': tm_temp_max,
#         'temp_graph': graph.get_temp_daily_graph(sensor_location=sensor_loc, graph_title=f'Temperatura @ {sensor_name}', the_date=_date)
#     }
#
#
#
#
#     _temp = information.get_temp(sensor_loc)
#     temp_chiminey = information.get_temp_chiminey()
#     temp_roof = information.get_temp_roof()
#     temp_garden = information.get_temp_garden()
#     temp_grass = information.get_temp_grass()
#
#     str_temp_external = f'{temp_external.temperature:.1f} {CELSIUS}' if temp_external else UNKNOWN
#     tm_temp_external = temp_external.timestamp.strftime('%H:%M') if temp_external else ''
#     str_temp_chiminey = f'{temp_chiminey.temperature:.1f} {CELSIUS}' if temp_chiminey else UNKNOWN
#     tm_temp_chiminey = temp_chiminey.timestamp.strftime('%H:%M') if temp_chiminey else ''
#     str_temp_roof = f'{temp_roof.temperature:.1f} {CELSIUS}' if temp_roof else UNKNOWN
#     tm_temp_roof = temp_roof.timestamp.strftime('%H:%M') if temp_roof else ''
#     str_temp_garden = f'{temp_garden.temperature:.1f} {CELSIUS}' if temp_garden else UNKNOWN
#     tm_temp_garden = temp_garden.timestamp.strftime('%H:%M') if temp_garden else ''
#     str_temp_grass = f'{temp_grass.temperature:.1f} {CELSIUS}' if temp_grass else UNKNOWN
#     tm_temp_grass = temp_grass.timestamp.strftime('%H:%M') if temp_grass else ''
#
#     temp_external_graph_svg = mark_safe(graph.get_temp_daily_graph(sensor_location=SENSOR_LOC_EXTERNAL,
#                                                                    graph_title='Temperatura zewnętrzna - czujnik pieca'))
#
#     context = {
#         'temp_external': str_temp_external,
#         'tm_temp_external': tm_temp_external,
#         'temp_chiminey': str_temp_chiminey,
#         'tm_temp_chiminey': tm_temp_chiminey,
#         'temp_roof': str_temp_roof,
#         'tm_temp_roof': tm_temp_roof,
#         'temp_garden': str_temp_garden,
#         'tm_temp_garden': tm_temp_garden,
#         'temp_grass': str_temp_grass,
#         'tm_temp_grass': tm_temp_grass,
#         'temp_external_graph': temp_external_graph_svg,
#         'date': _current_date
#     }
#
#     return HttpResponse(template.render(context, request))
