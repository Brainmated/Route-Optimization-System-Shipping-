import folium
from folium.plugins import BoatMarker


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

#Iterate through routes with route
for route in routes:
    start_port, end_port = route

    BoatMarker(
        [ports[0]["lat"], ports[0]["lon"]],
        [ports[0]["lat"], ports[0]["lon"]]
    ).add_to(m)

