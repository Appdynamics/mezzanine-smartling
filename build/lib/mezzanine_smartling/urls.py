from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^smartling_callback/$', 'mezzanine_smartling.views.smartling_callback', name='smartling_callback'),
]
