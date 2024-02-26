from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse
from .forms import SignUpForm
from .pathing import Pathing, GridMap
from django.contrib.auth.views import LoginView, LogoutView
from .utils import get_ports_from_csv
import folium
import os
import random
import requests
import json
from .ports import parse_ports
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import numpy as np

# Login view
def login_view(request):

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return render(request, "debug")
        
        else:
            return render(request, "login")
        

# Logout view
def logout_view(request):
    logout(request)
    return render(request, 'logout.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            # You can then redirect to the login page, for example
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def debug_view(request):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_filepath = os.path.join(script_dir, "data", "ports.csv")
    
    ports = parse_ports()

    hide_input_box = request.session.pop('hide_input_box', False)
    # Define the bounds of your grid (replace with your specific grid bounds)
    min_lat, max_lat = -90, 90  # Replace with the minimum and maximum latitude of your grid
    min_lon, max_lon = -180, 180  # Replace with the minimum and maximum longitude of your grid
    
    # Create a map object centered on the geographic midpoint with a starting zoom level
    #Always Mercator Projection
    m = folium.Map(
        location=[(max_lat + min_lat) / 2, (max_lon + min_lon) / 2],
        zoom_start=3,
        min_zoom=3,
        tiles="Cartodb Positron",
        max_bounds=[[min_lat, min_lon], [max_lat, max_lon]],  # This will restrict the view to the map's initial bounds
    )

    # Define the actual bounds based on your grid limits
    bounds = [[min_lat, min_lon], [max_lat, max_lon]]
    m.fit_bounds(bounds)  # Fit the map to the bounds

    grid_size = 1

    # Create horizontal lines (latitude lines)
    for lat in range(-90, 90, grid_size):
        folium.PolyLine([(lat, -180), (lat, 180)], color="blue", weight=0.1).add_to(m)

    # Create vertical lines (longitude lines)
    for lon in range(-180, 180, grid_size):
        folium.PolyLine([(-90, lon), (90, lon)], color="blue", weight=0.1).add_to(m)

    # Emphasize the boundaries (equator and prime meridian)
    folium.PolyLine([(0, -180), (0, 180)], color="red", weight=0.3).add_to(m)  # Equator
    folium.PolyLine([(-90, 0), (90, 0)], color="red", weight=0.3).add_to(m)  # Prime Meridian

    '''Generate two random locations and draw a line between them
    random_points = []
    feature_collection = {"type": "FeatureCollection", "features": []}
    for _ in range(2):
        random_lat = random.uniform(-90, 90)
        random_lon = random.uniform(-180, 180)
        random_points.append((random_lat, random_lon))  # Append the point to the list
        folium.Marker([random_lat, random_lon]).add_to(m)  # Create a marker for the random location
    
    # Draw a line between the two random points
    folium.PolyLine(random_points, color="blue", weight=2.5, opacity=0.8).add_to(m)
    '''

    '''--------Coastline Test------------------
    for coords in coast_coords:
        folium.PolyLine(coords, color="red", weight=2.5, opacity=0.8).add_to(m)
    
    # Create a GeoJSON feature for the point
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [random_lon, random_lat],
        },
        "properties": {},
    }
    feature_collection["features"].append(feature)
    '''

    # Render map to HTML
    init_map_html = m._repr_html_()

    context = {
        'map_html': init_map_html,
        'hide_input_box': hide_input_box,
        'ports': ports,
    }

    return render(request, 'debug.html', context)

@require_http_methods(["POST"])
def simulate(request):

    min_lat, max_lat = -90, 90 
    min_lon, max_lon = -180, 180 
    grid_size = 1

    #initialize resolution
    grid_map = GridMap(resolution=grid_size)

    #add the edges between the nodes
    grid_map.add_edges()

    m = folium.Map(
    location=[0, 0],
    zoom_start=3,
    min_zoom=3,
    tiles="Cartodb Positron",
    max_bounds=[[min_lat, min_lon], [max_lat, max_lon]],
)
    bounds = [[min_lat, min_lon], [max_lat, max_lon]]
    m.fit_bounds(bounds)  # Fit the map to the bounds
    
    #Create horizontal lines (latitude lines)
    for lat in range(-90, 90, grid_size):
        folium.PolyLine([(lat, -180), (lat, 180)], color="blue", weight=0.1).add_to(m)

    #Create vertical lines (longitude lines)
    for lon in range(-180, 180, grid_size):
        folium.PolyLine([(-90, lon), (90, lon)], color="blue", weight=0.1).add_to(m)

    #obtaining the straight_path
    m, formatted_distance = Pathing.straight_path(request, m)

    #obtaining the a_star path -------------------------------------------------------------------------------------------------------FIX
    #result = Pathing.a_star(request, grid_map)

    ''' 
    For comparison reasons, the following lines draw over my folium grid.
    Uncomment with caution because it's going to draw all your computational power.
    for node in grid_map.nodes.values():
        folium.CircleMarker(
            location=[node.lat, node.lon],
            radius=1,
            color='blue'
        ).add_to(m)

        for neighbor in node.neighbors:
            folium.PolyLine(
                locations=[(node.lat, node.lon), (neighbor.lat, neighbor.lon)],
                weight=1,
                color='green'
            ).add_to(m)
    '''
    try:
        dijkstra_path = Pathing.dijkstra(request, grid_map)
        folium.PolyLine(dijkstra_path, color="green", weight=2, opacity=1).add_to(m)
    except ValueError as e:
        print(f"Error in Dijkstra's algorithm: {e}")
    except TypeError as e:
        print(f"Type Error in Dijkstra's algorithm: {e}")



        
    # Serialize the map to HTML
    map_html = m._repr_html_()

    context = {
        "map_html": map_html,
        "simulation_run": True,
        "distance_km": formatted_distance,
        "locationA": request.POST.get("locationA"),
        "locationB": request.POST.get("locationB"),
    }

    # Pass the new map to the template
    return render(request, 'debug.html', context)