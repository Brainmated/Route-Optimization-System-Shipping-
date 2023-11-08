python

import folium
import requests

def get_wind_speed(lat, lon, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    response = requests.get(url).json()
    if response["cod"] == 200:
        wind_speed = response["wind"]["speed"]
        return wind_speed
    else:
        print("Error retrieving weather data.")
        return None

def main():
    # Replace with your OpenWeatherAPI key
    api_key = "YOUR_OPENWEATHERAPI_KEY"

    # Coordinates of the location (e.g., a point in the ocean)
    lat = 39.0
    lon = -80.0

    # Create a Folium map centered around the given location
    map_center = [lat, lon]
    my_map = folium.Map(location=map_center, zoom_start=10)

    # Get wind speed for the given coordinates
    wind_speed = get_wind_speed(lat, lon, api_key)
    if wind_speed is not None:
        # Add a marker to the map with wind speed information
        marker_text = f"Wind Speed: {wind_speed} m/s"
        folium.Marker(location=map_center, popup=marker_text).add_to(my_map)

    # Save the map to an HTML file
    my_map.save("weather_map.html")
    print("Map saved as weather_map.html")

if __name__ == "__main__":
    main()
