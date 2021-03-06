from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('temp/ext', views.external_temperature, name='temp_ext'),
    path('temp/int', views.internal_temperature, name='temp_int')
]
