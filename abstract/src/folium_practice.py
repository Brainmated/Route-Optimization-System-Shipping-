import folium
from folium.plugins import BoatMarker
import pandas as pd
#from qgis.core import *

data = pd.read_csv("E:/Programming in Python/data/World_port_Index.csv")


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


#EXTREMELY IMPORTANT WE MAKE A .HTML FILE, THIS WILL WORK WITH OUR DJANGO PROGRAMM

m.save("E:/Programming in Python/results/Reports/ship_map.html")
