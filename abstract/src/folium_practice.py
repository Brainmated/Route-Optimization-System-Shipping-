import folium
from folium.plugins import BoatMaker


#import ports from the csv
ports = [
    {"name": "Port A", "lat": 40.7128, "lon": -74.0060},
    {"name": "Port A", "lat": 51.5074, "lon": -0.1278}
]

#folium map centered on the center of the map

m = folium.Map(location=[0, 0], zoom_start=2)

#iterate through ports with port
for port in ports:
    folium.Maker(
        location=[port["lat"], port["long"]],
        popup=port["name"],
        icon=folium.Icon(icon="anchor")
    ).add_to(m)

#Sample ship routes
routes = [
    ("Port A", "port B")
]

