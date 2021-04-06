from django.http import HttpResponse, Http404, HttpResponseServerError
from django.template import loader
from django.apps import apps as django_apps
from .restinfo import *


def index(request):
    template = loader.get_template('index.html')

    information = MainPageInfo()

    # note: by convention, the rest-client do not raise any deliberated exceptions
    # if any sort of an error occurs, the client returns empty objects (None)
    # it is up to front-end to handle unknown information
    temp_internal = information.get_temp_internal()
    temp_external = information.get_temp_external()
    temp_bunker = information.get_temp_bunker()
    cesspit = information.get_cesspit_level()
    humidity_in = information.get_humidity_in()
    air_quality = information.get_air_quality()
    pressure = information.get_pressure()

    _unknown = '?'
    _celsius = '\u2103'

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

    str_temp_external = f'{temp_external.temperature:.1f} {_celsius}' if temp_external else _unknown
    str_temp_internal = f'{temp_internal.temperature:.1f} {_celsius}' if temp_internal else _unknown
    str_temp_bunker = f'{temp_bunker.temperature:.1f} {_celsius}' if temp_bunker else _unknown
    tm_temp_external = temp_external.timestamp.strftime('%H:%M') if temp_external else ''
    tm_temp_internal = temp_internal.timestamp.strftime('%H:%M') if temp_internal else ''
    tm_temp_bunker = temp_bunker.timestamp.strftime('%H:%M') if temp_bunker else ''

    str_humidity_in = f'{humidity_in.current_value:.0f}' if humidity_in else _unknown
    tenicon_hum_in = _tendency_icons[humidity_in.tendency if humidity_in else Tendency.STEADY]

    str_pressure = f'{pressure.current_value:.0f}' if pressure else _unknown
    tenicon_pressure = _tendency_icons[pressure.tendency if pressure else Tendency.STEADY]

    cesspit_state = _cesspit_states[cesspit.state] if cesspit else ''
    cesspit_level_label = f'{cesspit.original_reading.fill:.2f}' if cesspit else _unknown
    cesspit_level = str(int(cesspit.original_reading.fill)) if cesspit else '0'
    cesspit_reading_state = '' if not cesspit else 'KO' if cesspit.failure_detected else 'OK'
    tm_cesspit = cesspit.original_reading.timestamp.strftime('%H:%M') if cesspit else ''

    aq_pm_10_label = air_quality.pm_10 if air_quality else _unknown
    aq_pm_10_level = 0 if not air_quality else air_quality.pm_10 if air_quality.pm_10 <= 100 else 100
    aq_pm_10_color = '' if not air_quality \
        else 'bg-success' if air_quality.pm_10 < 100 \
        else 'bg-warning' if air_quality.pm_10 < 200 \
        else 'bg-danger'

    aq_pm_2_5_label = air_quality.pm_2_5 if air_quality else _unknown
    aq_pm_2_5_level = 0 if not air_quality else air_quality.pm_2_5 if air_quality.pm_2_5 <= 100 else 100
    aq_pm_2_5_color = '' if not air_quality \
        else 'bg-success' if air_quality.pm_2_5 < 100 \
        else 'bg-warning' if air_quality.pm_2_5 < 200 \
        else 'bg-danger'

    tm_aq = air_quality.original_reading.timestamp.strftime('%H:%M') if air_quality else ''

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
        'date': _current_date
    }

    return HttpResponse(template.render(context, request))
