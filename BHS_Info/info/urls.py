from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('temp/ext', views.external_temperature, name='temp_ext'),
    path('temp/int', views.internal_temperature, name='temp_int'),
    path('temp/any', views.any_temperature, name='any_temp'),
    path('cesspit', views.cesspit, name='cesspit'),
    path('sys_status', views.system_status, name='sys_status'),
]
