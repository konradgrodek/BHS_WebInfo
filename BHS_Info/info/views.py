from django.http import HttpResponse, Http404, HttpResponseServerError
from django.template import loader
from django.apps import apps as django_apps
import requests
from datetime import datetime
from . import restconfig

rest_configuration = restconfig.RestConfig()


def index(request):
    configuration = django_apps.get_app_config('info')

    template = loader.get_template('index.html')

    temp_url = rest_configuration.get_current_temperature_endpoint().get_url()

    if not temp_url:
        return HttpResponseServerError()

    resp = requests.get(temp_url)

    if resp.status_code != 200:
        raise Http404('Odczyt temperatury jest nieaktywny')

    sensors = resp.json()

    _date = datetime.today().strftime('%Y-%m-%d %H:%M')

    external = '?'
    internal = '?'
    bunker = '?'

    for sensor in sensors:
        if sensor.get('object'):
            obj = sensor.get('object')
            if obj.get('location') == 'External':
                external = obj.get('temperature')
            elif obj.get('location') == 'Office':
                internal = obj.get('temperature')
            elif obj.get('location') == 'Bunker':
                bunker = obj.get('temperature')

    context = {'external': external, 'internal': internal, 'bunker': bunker, 'date': _date}

    return HttpResponse(template.render(context, request))