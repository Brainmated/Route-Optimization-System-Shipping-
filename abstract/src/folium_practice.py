import folium
from folium.plugins import BoatMarker
import pandas as pd
import time
import schedule
#from qgis.core import *

data = pd.read_csv("E:/Programming in Python/data/World_port_Index.csv")

# Schedule the weather data update every hour
schedule.every().hour.do(update_weather_data)

# Run the scheduled updates indefinitely
#This will loop every hour to give new weather updates for the marks
while True:
    schedule.run_pending()
    time.sleep(1)

#import ports from the csv
ports = [
    {"name": "Port A", "lat": 40.7128, "lon": -74.0060},
    {"name": "Port B", "lat": 51.5074, "lon": -0.1278}
]

#folium map centered on the center of the map

m = folium.Map(location=[0, 0], zoom_start=2)

#iterate through ports with port
for port in ports:
    folium.Marker(
        location=[port["lat"], port["lon"]],
        popup=port["name"],
        icon=folium.Icon(icon="anchor")
    ).add_to(m)

    locations = [[port["lat"], port["lon"]] for port in ports]
    line = folium.PolyLine(locations=locations, color='blue')
    m.add_child(line)

#Sample ship routes
routes = [
    ("Port A", "port B")
]

#Iterate through routes with route
for route in routes:
    start_port, end_port = route

    BoatMarker(
        [ports[0]["lat"], ports[0]["lon"]],
        [ports[0]["lat"], ports[0]["lon"]],
        color ="FF0000",
        heading_in_degrees=90,
        wind_heading_in_degrees=0
    ).add_to(m)

'''This is a test. AND IT FUCKING WORKS.'''
# Create a custom HTML form for user input
form_html = """
<div style="position: fixed; top: 10px; left: 10px; background-color: white; padding: 10px; z-index: 9999;">
    <form id="port-form">
        <label for="port-a">Port A:</label>
        <input type="text" id="port-a" name="port-a" placeholder="Enter Port A"><br><br>
        <label for="port-b">Port B:</label>
        <input type="text" id="port-b" name="port-b" placeholder="Enter Port B"><br><br>
        <input type="submit" value="Submit">
    </form>
</div>
"""
#This is the method which will constantly update the weather markers
def update_weather_data():
    # Fetch the latest weather data from the API
    weather_data = requests.get(api_url).json()

    # Remove existing markers from the map
    map.remove()

    # Add new markers with updated weather information
    for location in weather_data['locations']:
        lat = location['latitude']
        lon = location['longitude']
        weather_info = location['weather']

        # Create a marker with updated weather information
        marker = folium.Marker(location=[lat, lon], popup=weather_info)
        marker.add_to(map)


# Add the custom HTML form to the map
m.get_root().html.add_child(folium.Element(form_html))

#EXTREMELY IMPORTANT WE MAKE A .HTML FILE, THIS WILL WORK WITH OUR DJANGO PROGRAMM

m.save("E:/Programming in Python/results/Reports/ship_map.html")
