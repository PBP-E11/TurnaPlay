from django.urls import path, include
from tournaments.views import show_main

app_name = 'tournaments'

urlpatterns = [
    path('', show_main, name='show_main'),
]