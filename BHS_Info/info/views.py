from django.http import HttpResponse, HttpResponseBadRequest
from django.template import loader

from datetime import timedelta
from functools import reduce

import logging as log

from .restinfo import *

UNKNOWN = '?'
UNKNOWN_ICON = 'question.svg'
CELSIUS = '\u2103'
REQUEST_DATE_FORMAT = '%Y-%m-%d'


def index(request):
    template = loader.get_template('index.html')

    information = MainPageInfo()

    # note: by convention, the rest-client do not raise any deliberated exceptions
    # if any sort of an error occurs, the client returns Error or NotAvailable beans
    # it is up to front-end to handle unknown information
    temp_internal = information.get_temp_internal()
    temp_external = information.get_temp_external_best_available()
    temp_bunker = information.get_temp_bunker()
    cesspit = information.get_cesspit_level()
    cesspit_prediction = information.get_cesspit_prediction()
    humidity_in = information.get_humidity_in()
    air_quality = information.get_air_quality()
    pressure = information.get_pressure()
    daylight = information.get_daylight()
    solar_plant = information.get_solar_plant()
    precipitation = information.get_precipitation()
    wind = information.get_wind()
    water_tank = information.get_water_tank()
    system_status = information.get_system_status()
    progress_bars = ProgressBar()
    progress_bar_size = (4, 0.32)

    _current_date = datetime.today().strftime('%Y-%m-%d %H:%M')
    _short_date = datetime.today().strftime(REQUEST_DATE_FORMAT)

    _tendency_icons = {
        Tendency.RISING: 'arrow-up-right.svg',
        Tendency.STEADY: 'arrow-right.svg',
        Tendency.FALLING: 'arrow-down-right.svg'
    }

    str_temp_external = f'{temp_external.temperature:.1f} {CELSIUS}' if temp_external.has_succeeded() else UNKNOWN
    str_temp_internal = f'{temp_internal.temperature:.1f} {CELSIUS}' if temp_internal.has_succeeded() else UNKNOWN
    str_temp_bunker = f'{temp_bunker.temperature:.1f} {CELSIUS}' if temp_bunker.has_succeeded() else UNKNOWN
    tm_temp_external = temp_external.timestamp.strftime('%H:%M') if temp_external.has_succeeded() else ''
    tm_temp_internal = temp_internal.timestamp.strftime('%H:%M') if temp_internal.has_succeeded() else ''
    tm_temp_bunker = temp_bunker.timestamp.strftime('%H:%M') if temp_bunker.has_succeeded() else ''

    str_humidity_in = f'{humidity_in.current_value:.0f}' if humidity_in.has_succeeded() else UNKNOWN
    tenicon_hum_in = _tendency_icons[humidity_in.tendency if humidity_in.has_succeeded() else Tendency.STEADY]

    str_pressure = f'{pressure.current_value:.0f}' if pressure.has_succeeded() else UNKNOWN
    tenicon_pressure = _tendency_icons[pressure.tendency if pressure.has_succeeded() else Tendency.STEADY]

    cesspit_progress = progress_bars.get_progress_bar(
        cesspit.original_reading.fill if cesspit.has_succeeded() else 0, size=progress_bar_size, colormap='RdYlGn_r')
    cesspit_reading_state = '' if not cesspit.has_succeeded() else 'KO' if cesspit.failure_detected else 'OK'
    tm_cesspit = cesspit.original_reading.timestamp.strftime('%H:%M') if cesspit.has_succeeded() else ''
    cesspit_predicted_full_date = cesspit_prediction.predicted_date.strftime('%Y-%m-%d %H:%M') if cesspit_prediction.has_succeeded() else '?'

    aq_pm_10_norm_perc = progress_bars.get_progress_bar(
        percentage=air_quality.pm_10 if air_quality.has_succeeded() else 0, size=progress_bar_size, colormap='RdYlGn_r')
    aq_pm_10_level = UNKNOWN if not air_quality.has_succeeded() \
        else (str(air_quality.original_reading.pm_10)+' \u03bcg/m\u00b3')

    aq_pm_2_5_norm_perc = progress_bars.get_progress_bar(
        percentage=air_quality.pm_2_5 if air_quality.has_succeeded() else 0, size=progress_bar_size, colormap='RdYlGn_r')
    aq_pm_2_5_level = UNKNOWN if not air_quality.has_succeeded() \
        else (str(air_quality.original_reading.pm_2_5)+' \u03bcg/m\u00b3')

    tm_aq = air_quality.original_reading.timestamp.strftime('%H:%M') if air_quality.has_succeeded() else ''

    if precipitation.has_succeeded() and precipitation.is_raining:
        sky_state_icon = 'cloud-rain.svg'  # heavy?
    elif daylight.has_succeeded():
        if daylight.time_of_day == TimeOfDay.NIGHT:
            sky_state_icon = 'moon.svg'
        elif daylight.original_reading.is_sunlight:
            sky_state_icon = 'sun.svg'
        elif daylight.time_of_day == TimeOfDay.MORNING:
            sky_state_icon = 'sunrise.svg'
        elif daylight.time_of_day == TimeOfDay.EVENING:
            sky_state_icon = 'sunset.svg'
        else:
            sky_state_icon = 'clouds.svg'  # cloud-sun?
    else:
        sky_state_icon = 'question.svg'

    soil_hums = information.get_soil_moisture()
    if type(soil_hums) == list:
        tenicons_shum = [_tendency_icons[soil_hum.tendency] for soil_hum in soil_hums]
        strs_shum = [f'{soil_hum.current_value:.1f}' for soil_hum in soil_hums]
    else:
        tenicons_shum = [UNKNOWN_ICON for _i in range(3)]
        strs_shum = [UNKNOWN for _i in range(3)]

    tm_sol = solar_plant.reading.last_production_at.strftime('%Y-%m-%d %H:%M') if solar_plant.has_succeeded() and solar_plant.reading.last_production_at else UNKNOWN
    sol_prod_now_w = str(solar_plant.reading.current_production_w) if solar_plant.has_succeeded() else UNKNOWN
    sol_prod_now_perc = str(solar_plant.current_production_perc) if solar_plant.has_succeeded() else '0'
    sol_prod_now_progress_bar = progress_bars.get_progress_bar(
        percentage=solar_plant.current_production_perc if solar_plant.has_succeeded() else 0,
        size=progress_bar_size, show_border=False, colormap='Greens')
    sol_prod_today = f'{solar_plant.reading.daily_production_kwh:.1f}' if solar_plant.has_succeeded() else UNKNOWN
    sol_prod_h_min_w = str(solar_plant.reading.hourly_min_w) if solar_plant.has_succeeded() else UNKNOWN
    sol_prod_h_min_perc = str(solar_plant.hourly_min_perc) if solar_plant.has_succeeded() else '0'
    sol_prod_h_avg_w = str(solar_plant.reading.hourly_avg_w) if solar_plant.has_succeeded() else UNKNOWN
    sol_prod_h_avg_perc = str(solar_plant.hourly_avg_perc) if solar_plant.has_succeeded() else '0'
    sol_prod_h_max_w = str(solar_plant.reading.hourly_max_w) if solar_plant.has_succeeded() else UNKNOWN
    sol_prod_h_max_perc = str(solar_plant.hourly_max_perc) if solar_plant.has_succeeded() else '0'

    # wind direction
    _wind_direction_icons = {
        WindDirection.S: 'arrow-up-circle.svg',
        WindDirection.SE: 'arrow-up-right-circle.svg',
        WindDirection.W: 'arrow-left-circle.svg',
        WindDirection.NE: 'arrow-down-right-circle.svg',
        WindDirection.N: 'arrow-down-circle.svg',
        WindDirection.NW: 'arrow-down-left-circle.svg',
        WindDirection.E: 'arrow-right-circle.svg',
        WindDirection.SW: 'arrow-up-left-circle.svg',
        WindDirection.UNKNOWN: 'question-circle.svg'
    }
    # take direction and peak from long-term observations, current speed from short-term
    wind_dir = wind.long_term_observation.direction if wind.has_succeeded() else WindDirection.UNKNOWN
    wind_dir_icon = _wind_direction_icons[wind_dir]
    wind_dir_var = f'{int(wind.long_term_observation.direction_var)}%' if wind.has_succeeded() else ''
    wind_peak = f'{int(wind.long_term_observation.wind_peak)} km/h' if wind.has_succeeded() else UNKNOWN
    wind_speed = f'{int(wind.short_term_observation.wind_speed)} km/h' if wind.has_succeeded() else UNKNOWN
    # wind_speed_var = f'{int(wind.short_term_observation.wind_variance)}%' if wind.has_succeeded() else UNKNOWN

    # precipitation
    rain_mm = f'{precipitation.precipitation_mm:.1f} mm' if precipitation.has_succeeded() else UNKNOWN
    rain_obs_h = f'{precipitation.observation_duration_h} h' if precipitation.has_succeeded() else UNKNOWN

    # water tank
    water_level = progress_bars.get_progress_bar(
        percentage=int(water_tank.fill if water_tank.has_succeeded() else 0),
        size=progress_bar_size, show_border=False, colormap='Greens')
    tm_water_level = water_tank.timestamp.strftime('%H:%M') if water_tank.has_succeeded() else UNKNOWN

    # system status
    _icon_internet_ok = 'globe-green.svg'
    _icon_internet_ko = 'globe-red.svg'
    _icon_db_ok = 'database-fill-check.svg'
    _icon_db_ko = 'database-fill-down.svg'
    _icon_services_ok = 'check-circle-fill.svg'
    _icon_services_ko = 'exclamation-circle-fill-red.svg'
    _icon_services_warn = 'exclamation-circle-fill-orange.svg'

    internet_icon = _icon_internet_ok if system_status.has_succeeded() \
        and system_status.internet_connection_status.has_succeeded() \
        and system_status.internet_connection_status.alive \
        else _icon_internet_ko
    if system_status.has_succeeded() and system_status.internet_connection_status.has_succeeded():
        internet_download = f"{int(system_status.internet_connection_status.download_kbps/1000)}M" \
            if system_status.internet_connection_status.download_kbps is not None else UNKNOWN
        internet_upload = f"{int(system_status.internet_connection_status.upload_kbps/1000)}M" \
            if system_status.internet_connection_status.upload_kbps is not None else UNKNOWN
        internet_ping = f"{system_status.internet_connection_status.ping_microseconds/1000:.1f}ms" \
            if system_status.internet_connection_status.ping_microseconds is not None else UNKNOWN
    else:
        internet_download = UNKNOWN
        internet_upload = UNKNOWN
        internet_ping = UNKNOWN

    internet_tm = (
        system_status.internet_connection_status if system_status.has_succeeded() else system_status
    ).timestamp.strftime('%H:%M')

    _activities_state = [_activity_state.state for _activity_state in reduce(
        lambda x, y: x+y,
        [_status.activities_state for _status in system_status.service_statuses]
    )] if system_status.has_succeeded() else []

    activities_up = sum([1 if _state in (ServiceActivityState.OK, ServiceActivityState.STARTING) else 0
                         for _state in _activities_state])
    activities_down = sum([1 if _state in (ServiceActivityState.NOT_AVAILABLE, ServiceActivityState.DEAD) else 0
                           for _state in _activities_state])
    activities_warn = sum([1 if _state == ServiceActivityState.WARNING else 0
                           for _state in _activities_state])
    activities_icon = _icon_services_ok if activities_down+activities_warn == 0 and activities_up > 0 \
        else _icon_services_ko if activities_down > 0 or activities_up == 0 else _icon_services_warn

    database_icon = _icon_db_ok if system_status.has_succeeded() and system_status.database_status.has_succeeded() \
        and system_status.database_status.is_available else _icon_db_ko

    system_status_tm = system_status.timestamp.strftime('%H:%M')

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
        'cesspit_progress': cesspit_progress,
        'cesspit_reading_state': cesspit_reading_state,
        'cesspit_predicted_full_date': cesspit_predicted_full_date,
        'tm_cesspit': tm_cesspit,
        'aq_pm_10_norm_perc': aq_pm_10_norm_perc,
        'aq_pm_10_level': aq_pm_10_level,
        'aq_pm_2_5_norm_perc': aq_pm_2_5_norm_perc,
        'aq_pm_2_5_level': aq_pm_2_5_level,
        'tm_aq': tm_aq,
        'sunrise': daylight.sunrise if daylight.has_succeeded() else UNKNOWN,
        'sunset': daylight.sunset if daylight.has_succeeded() else UNKNOWN,
        'sky_state_icon': sky_state_icon,
        'daylight_perc': daylight.original_reading.luminescence_perc if daylight.has_succeeded() else UNKNOWN,
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
        'wind_dir': wind_dir.name if wind_dir != WindDirection.UNKNOWN else UNKNOWN,
        'wind_dir_icon': wind_dir_icon,
        'wind_dir_var': wind_dir_var,
        'wind_speed': wind_speed,
        'wind_peak': wind_peak,
        'rain_mm': rain_mm,
        'rain_obs_h': rain_obs_h,
        'date': _current_date,
        'date_short': _short_date,
        'water_tank_progress': water_level,
        'tm_water_tank_level': tm_water_level,
        'internet_icon': internet_icon,
        'internet_download': internet_download,
        'internet_upload': internet_upload,
        'internet_ping': internet_ping,
        'internet_tm': internet_tm,
        'activities_up': activities_up,
        'activities_down': activities_down,
        'activities_warn': activities_warn,
        'activities_icon': activities_icon,
        'database_icon': database_icon,
        'system_status_tm': system_status_tm,
    }

    return HttpResponse(template.render(context, request))


def external_temperature(request):
    template = loader.get_template('temperatures_ext.html')

    information = TemperatureInfo()
    graph = TemperatureGraph()

    _current_date = datetime.today().strftime('%Y-%m-%d %H:%M')
    _short_date = datetime.today().strftime(REQUEST_DATE_FORMAT)

    temp_external = information.get_temp_external()
    temp_chimney = information.get_temp_chimney()
    temp_roof = information.get_temp_roof()
    temp_garden = information.get_temp_garden()
    temp_grass = information.get_temp_grass()

    str_temp_external = f'{temp_external.temperature:.1f} {CELSIUS}' if temp_external.has_succeeded() else UNKNOWN
    tm_temp_external = temp_external.timestamp.strftime('%H:%M') if temp_external.has_succeeded() else ''
    str_temp_chimney = f'{temp_chimney.temperature:.1f} {CELSIUS}' if temp_chimney.has_succeeded() else UNKNOWN
    tm_temp_chimney = temp_chimney.timestamp.strftime('%H:%M') if temp_chimney.has_succeeded() else ''
    str_temp_roof = f'{temp_roof.temperature:.1f} {CELSIUS}' if temp_roof.has_succeeded() else UNKNOWN
    tm_temp_roof = temp_roof.timestamp.strftime('%H:%M') if temp_roof.has_succeeded() else ''
    str_temp_garden = f'{temp_garden.temperature:.1f} {CELSIUS}' if temp_garden.has_succeeded() else UNKNOWN
    tm_temp_garden = temp_garden.timestamp.strftime('%H:%M') if temp_garden.has_succeeded() else ''
    str_temp_grass = f'{temp_grass.temperature:.1f} {CELSIUS}' if temp_grass.has_succeeded() else UNKNOWN
    tm_temp_grass = temp_grass.timestamp.strftime('%H:%M') if temp_grass.has_succeeded() else ''

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
        'date': _current_date,
        'date_short': _short_date
    }

    return HttpResponse(template.render(context, request))


def internal_temperature(request):
    template = loader.get_template('temperatures_int.html')

    information = TemperatureInfo()
    graph = TemperatureGraph()

    _current_date = datetime.today().strftime('%Y-%m-%d %H:%M')
    _short_date = datetime.today().strftime(REQUEST_DATE_FORMAT)

    temp_office = information.get_temp_office()
    temp_attic = information.get_temp_attic()
    temp_bunker = information.get_temp_bunker()
    temp_garage = information.get_temp_garage()

    str_temp_office = f'{temp_office.temperature:.1f} {CELSIUS}' if temp_office.has_succeeded() else UNKNOWN
    tm_temp_office = temp_office.timestamp.strftime('%H:%M') if temp_office.has_succeeded() else ''
    str_temp_attic = f'{temp_attic.temperature:.1f} {CELSIUS}' if temp_attic.has_succeeded() else UNKNOWN
    tm_temp_attic = temp_attic.timestamp.strftime('%H:%M') if temp_attic.has_succeeded() else ''
    str_temp_bunker = f'{temp_bunker.temperature:.1f} {CELSIUS}' if temp_bunker.has_succeeded() else UNKNOWN
    tm_temp_bunker = temp_bunker.timestamp.strftime('%H:%M') if temp_bunker.has_succeeded() else ''
    str_temp_garage = f'{temp_garage.temperature:.1f} {CELSIUS}' if temp_garage.has_succeeded() else UNKNOWN
    tm_temp_garage = temp_garage.timestamp.strftime('%H:%M') if temp_garage.has_succeeded() else ''

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
        'date': _current_date,
        'date_short': _short_date
    }

    return HttpResponse(template.render(context, request))


def any_temperature(request):
    sensor_loc = request.GET.get('sensor')
    sensor_name = request.GET.get('name')
    req_date = request.GET.get('date')

    if not sensor_loc:
        return HttpResponseBadRequest()

    if not sensor_name:
        sensor_name = UNKNOWN

    _date = datetime.today()
    if req_date:
        _date = datetime.strptime(req_date, REQUEST_DATE_FORMAT)

    _is_today = (datetime.today() - _date).days < 1

    _date_minus = _date - timedelta(days=1)
    _date_plus = _date + timedelta(days=1)

    _str_date = _date.strftime(REQUEST_DATE_FORMAT)
    _str_date_minus = _date_minus.strftime(REQUEST_DATE_FORMAT)
    _str_date_plus = _date_plus.strftime(REQUEST_DATE_FORMAT)

    template = loader.get_template('temperature.html')

    stats = TemperatureDailyStatistics().get_daily_statistics(sensor_location=sensor_loc, the_date=_date)
    graph = TemperatureGraph()

    context = {
        'sensor_name': sensor_name,
        'sensor_loc': sensor_loc,
        'is_today': _is_today,
        'the_date': _date.strftime('%Y-%m-%d'),
        'date_minus': _date_minus.strftime('%Y-%m-%d'),
        'date_plus': _date_plus.strftime('%Y-%m-%d'),
        'temp_graph': graph.get_temp_daily_graph(
            sensor_location=sensor_loc, graph_title=None, the_date=_date),
        'daily_min': f'{stats.statistics_24h.temp_min:.1f} {CELSIUS}' if stats.has_succeeded() else UNKNOWN,
        'daily_min_tm': f'{stats.statistics_24h.min_at.strftime("%H:%M")}' if stats.has_succeeded() else UNKNOWN,
        'daily_avg': f'{stats.statistics_24h.temp_avg:.1f} {CELSIUS}' if stats.has_succeeded() else UNKNOWN,
        'daily_max': f'{stats.statistics_24h.temp_max:.1f} {CELSIUS}' if stats.has_succeeded() else UNKNOWN,
        'daily_max_tm': f'{stats.statistics_24h.max_at.strftime("%H:%M")}' if stats.has_succeeded() else UNKNOWN,
        'day_min': f'{stats.statistics_day.temp_min:.1f} {CELSIUS}' if stats.has_succeeded() else UNKNOWN,
        'day_min_tm': f'{stats.statistics_day.min_at.strftime("%H:%M")}' if stats.has_succeeded() and stats.statistics_day.has_succeeded() else UNKNOWN,
        'day_avg': f'{stats.statistics_day.temp_avg:.1f} {CELSIUS}' if stats.has_succeeded() and stats.statistics_day.has_succeeded() else UNKNOWN,
        'day_max': f'{stats.statistics_day.temp_max:.1f} {CELSIUS}' if stats.has_succeeded() and stats.statistics_day.has_succeeded() else UNKNOWN,
        'day_max_tm': f'{stats.statistics_day.max_at.strftime("%H:%M")}' if stats.has_succeeded() and stats.statistics_day.has_succeeded() else UNKNOWN,
        'night_min': f'{stats.statistics_night.temp_min:.1f} {CELSIUS}' if stats.has_succeeded() and stats.statistics_night.has_succeeded() else UNKNOWN,
        'night_min_tm': f'{stats.statistics_night.min_at.strftime("%H:%M")}' if stats.has_succeeded() and stats.statistics_night.has_succeeded() else UNKNOWN,
        'night_avg': f'{stats.statistics_night.temp_avg:.1f} {CELSIUS}' if stats.has_succeeded() and stats.statistics_night.has_succeeded() else UNKNOWN,
        'night_max': f'{stats.statistics_night.temp_max:.1f} {CELSIUS}' if stats.has_succeeded() and stats.statistics_night.has_succeeded() else UNKNOWN,
        'night_max_tm': f'{stats.statistics_night.max_at.strftime("%H:%M")}' if stats.has_succeeded() and stats.statistics_night.has_succeeded() else UNKNOWN
    }

    return HttpResponse(template.render(context, request))


def cesspit(request):
    template = loader.get_template('cesspit.html')

    information = CesspitInfo()
    graph = CesspitGraph()
    progress_bar = ProgressBar()

    progress_bar_size = (4, 0.32)

    _current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    _short_date = datetime.today().strftime(REQUEST_DATE_FORMAT)

    r_level = information.get_cesspit_level()
    r_prediction = information.get_cesspit_prediction()
    r_log = information.get_cesspit_log()

    cesspit_progress = progress_bar.get_progress_bar(
        r_level.original_reading.fill if r_level.has_succeeded() else 0, size=progress_bar_size, colormap='RdYlGn_r')
    cesspit_reading_state = '' if not r_level.has_succeeded() else 'KO' if r_level.failure_detected else 'OK'
    tm_cesspit = r_level.original_reading.timestamp.strftime('%H:%M') if r_level.has_succeeded() else ''
    cesspit_predicted_full_date = r_prediction.predicted_date.strftime('%Y-%m-%d %H:%M') \
        if r_prediction.has_succeeded() else UNKNOWN
    cesspit_predicted_in_days = str((r_prediction.predicted_date - datetime.now()).days) \
        if r_prediction.has_succeeded() else UNKNOWN
    cesspit_predicted_at = r_prediction.as_of_date.strftime('%H:%M') \
        if r_prediction.has_succeeded() else UNKNOWN
    # cesspit_log = [f'<p class="fs-6 text-break>{l}</p>' for l in r_log.log_entries] \
    #     if r_log.has_succeeded() else []
    cesspit_log = list(reversed(r_log.log_entries)) if r_log.has_succeeded() else []

    graph_today_svg = mark_safe(graph.get_today_usage_graph())
    graph_week_svg = mark_safe(graph.get_last_week_usage_graph())
    graph_prediction_svg = mark_safe(graph.get_prediction_graph())

    context = {
        'date': _current_date,
        'date_short': _short_date,
        'cesspit_progress': cesspit_progress,
        'cesspit_reading_state': cesspit_reading_state,
        'cesspit_predicted_full_date': cesspit_predicted_full_date,
        'cesspit_predicted_at': cesspit_predicted_at,
        'cesspit_predicted_in_days': cesspit_predicted_in_days,
        'cesspit_log': cesspit_log,
        'tm_cesspit': tm_cesspit,
        'graph_today': graph_today_svg,
        'graph_this_week': graph_week_svg,
        'graph_prediction': graph_prediction_svg,
    }

    return HttpResponse(template.render(context, request))


def system_status(request):
    template = loader.get_template('system_status.html')

    _icon_internet_ok = 'globe-green.svg'
    _icon_internet_ko = 'globe-red.svg'
    _icon_db_ok = 'database-fill-check.svg'
    _icon_db_ko = 'database-fill-down.svg'
    _icon_services_ok = 'check-circle-fill.svg'
    _icon_services_ko = 'exclamation-circle-fill-red.svg'
    _icon_services_warn = 'exclamation-circle-fill-orange.svg'

    information = SystemStatusInfo()
    status = information.get_system_status()
    inet = status.internet_connection_status \
        if status.has_succeeded() and status.internet_connection_status.has_succeeded() else None

    components = [(
        'Baza danych',
        'RPiCopper',  # hard-coded; maybe should be not here, but in REST?
        _icon_db_ok if status.has_succeeded() and status.database_status is not None and status.database_status.is_available
        else _icon_db_ko,
        (status.timestamp if not status.has_succeeded() or status.database_status is None
         else status.database_status.timestamp).strftime('%H:%M'),
        UNKNOWN if not status.has_succeeded() or status.database_status is None
        else " | ".join([msg for msg in (status.database_status.connected_to, status.database_status.log, status.database_status.issue) if msg is not None])
    )]

    if status.has_succeeded() and status.service_statuses is not None:
        for _service in status.service_statuses:
            components.extend([
                (
                    _a.name if len(_service.activities_state) < 2 else f"{_a.name}|{_service.name}",
                    _service.hostname if _service.hostname is not None else UNKNOWN,
                    _icon_services_ok if _a.state == ServiceActivityState.OK else
                    _icon_services_ko if _a.state == ServiceActivityState.DEAD else
                    _icon_services_warn if _a.state == ServiceActivityState.WARNING else
                    UNKNOWN_ICON,
                    _a.timestamp.strftime('%H:%M' if (datetime.now() - _a.timestamp).total_seconds() < 24*60*60
                                          else '%Y-%m-%d %H:%m'),
                    _a.message if _a.message is not None else UNKNOWN,
                )
                for _a in _service.activities_state
            ])

    servers = list()
    if status.has_succeeded() and status.host_statuses is not None:
        servers = [
            (
                host_status.host_name,  # 0
                host_status.timestamp.strftime('%Y-%m-%d %H:%M'),  # 1
                _time_lapsed(host_status.boot_time),  # 2
                _icon_services_ok if host_status.up else _icon_services_ko  # 3
            )
            for host_status in status.host_statuses
        ]

    context = {
        "the_date": status.timestamp.strftime('%Y-%m-%d %H:%M'),
        "inet_date": (inet.timestamp if inet is not None else status.timestamp).strftime('%Y-%m-%d %H:%M'),
        "inet_icon": UNKNOWN_ICON if inet is None else _icon_internet_ok if inet.alive else _icon_internet_ko,
        "inet_up": UNKNOWN if inet is None else f"{int(inet.upload_kbps / 1000)} Mbps",
        "inet_down": UNKNOWN if inet is None else f"{int(inet.download_kbps / 1000)} Mbps",
        "inet_ping": UNKNOWN if inet is None else f"{inet.ping_microseconds / 1000:.3f} ms",
        "inet_jitter": UNKNOWN if inet is None else f"{inet.jitter_microseconds / 1000:.3f} ms",
        "inet_ip": UNKNOWN if inet is None or inet.external_ip is None else inet.external_ip,
        "components": components,
        "servers": servers
    }

    return HttpResponse(template.render(context, request))


def _time_lapsed(start_time: datetime) -> str:
    if start_time is None:
        return UNKNOWN
    delta = datetime.now() - start_time
    hours = round(delta.total_seconds()) // (60*60)
    days = (hours // 24) % 7
    weeks = (hours // 24) // 7
    hours = hours % 24
    days = "" if days < 1 else f"{days} dni, "
    weeks = "" if weeks < 1 else f"{weeks} tygodni, "
    return f"{weeks}{days}{hours} godzin"
