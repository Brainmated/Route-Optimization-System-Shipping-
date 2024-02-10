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
    
