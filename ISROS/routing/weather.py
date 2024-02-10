import requests
from config import API_KEY
from pathing import get_path_coordinates

STORM_GLASS_API_ENDPOINT = 'https://api.stormglass.io/v2/weather/point'

def get_weather_data(latitude, longitude):
    params =v{
        "lat":latitude,
        "lon":longitude,
        "params": ",".join(["airTemperature", "windSpeed", "waveheight"]),
        #check if anything else should be added
    }

    headers = {
        "Authorization": API_KEY
    }

    response = requests.get(STORM_GLASS_API_ENDPOINT, params=params, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error for data: ({latitude}, {longitude})")
        return None
    
def generate_weather_map(path_coordinates):
    weather_data = []

    for coord in path_coordinates:
        data = get_weather_data(coord["latitude"], coord["longitude"])

        if data:
            weather_data.append({
                "lat":coord["latitude"],
                "lon": coord["longitude"],
                "airTemperature": data["hours"][0]["airTemperature"]["noaa"],
                "windSpeed": data["hours"][0]["windSpeed"]["noaa"],
                "waveHeight": data["hours"][0]["waveHeight"]["noaa"],
                #maybe something else, i dont know
            })
    #Integrate the data in the debug.html, find a way
    #just print for now
    for item in weather_data:
        print(item)
    
    #if get_path_coordinates from pathing.py return coordinates like:
    #[{"latitude": 59.91, "longitude":10.75}, "latitude": 59.92, "longitude":10.76}]
    path_coordinates = get_path_coordinates()
    generate_weather_map(path_coordinates)