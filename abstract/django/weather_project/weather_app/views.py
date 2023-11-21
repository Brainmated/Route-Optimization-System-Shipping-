import requests
import datetime
from django.shortcuts import render


# Create your views here.
def index(request):
    API_KEY = open("API_KEY", "r").read()
    current_weather_url = "http://api.openweathermap.org/data/2.5/weather?q={}&appid={}"
    forecast_url = "http://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&exclude=current,minutely,hourly,alerts&appid={}"

    if request.method == "POST":
        city1 = request.POST["city1"]
        city2 = request.get("city2", None)
        pass
    else:
        return render(request, "weather_app/index.html")
    
def fetch_weather_and_forecast(city, api_key, current_weather_url, forecast_url):
    #send to the api and get responses
    response = requests.get(current_weather_url.format(city, api_key)).json() #as a dictionary
    lat, lon = response["coord"]["lat"], response["coord"]["lon"]
    forecast_response = requests.get(forecast_url.format(lat, lon, api_key)).json

    #format to be readable

    weather_data = {
        "city": city,
        "temperature": round(response["main"]["temp"]),
        "description": response["weather"][0]["description"],
        "icon": response["weather"][0]["icon"]
    }