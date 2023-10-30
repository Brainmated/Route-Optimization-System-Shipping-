import folium
from folium.plugins import BoatMarker


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

    # Get the coordinates of the start and end ports
    start_lat = next(port["lat"] for port in ports if port["name"] == start_port)
    start_lon = next(port["lon"] for port in ports if port["name"] == start_port)
    end_lat = next(port["lat"] for port in ports if port["name"] == end_port)
    end_lon = next(port["lon"] for port in ports if port["name"] == end_port)

    folium.PolyLine(
        locations=[[start_lat, start_lon], [end_lat, end_lon]],
        color="blue",
        weight=2
    ).add_to(m)
