import requests
import datetime
from django.shortcuts import render


# Create your views here.
def index(request):
    API_KEY = open("API_KEY", "r").read()
    current_weather_url = "http://api.openweathermap.org/data/2.5/weather?q={}&appid={}"
    forecast_url = "http://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&exclude=current,minutely,hourly,alerts&appid={}"

    if request.method == "POST":
        pass
    else:
        return render()