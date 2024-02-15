from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse
from .forms import SignUpForm
from .pathing import Pathing, GridMap, Map_Marking
from .ports import parse_ports
from django.contrib.auth.views import LoginView, LogoutView
from .utils import get_ports_from_csv
import folium
import os
import random
import requests
import json
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

@require_http_methods(["POST"])
def simulate(request):
    loc_a_name = request.POST.get("locationA")
    loc_b_name = request.POST.get("locationB")

    ports = parse_ports()
    loc_a = next((item for item in ports if item["name"] == loc_a_name), None)
    loc_b = next((item for item in ports if item["name"] == loc_b_name), None)

    #conver lat and lot to float for tuples

    loc_a_coords = (float(loc_a["latitude"]), float(loc_a["longitude"]))
    loc_b_coords = (float(loc_b["latitude"]), float(loc_b["longitude"]))

    m = request.session.get("map", folium.Map(location=[0, 0], zoom_start=2))
    
    #draw line
    Pathing.straight_path(m, loc_a_coords, loc_b_coords)

    #redirect
    return HttpResponseRedirect(reverse("debug"))
def debug_view(request):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_filepath = os.path.join(script_dir, "data", "ports.csv")
    
    ports = parse_ports()
    land_shp = os.path.join(script_dir, "data", "ne_10m_land.shp")
    coastline_shp = os.path.join(script_dir, "data", "ne_10m_coastline.shp")
    
    #test coords of land, 1st parameter for pathing
    coast_coords = Pathing.is_coast()

    #-------------------------

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
    map_html = m._repr_html_()

    context = {
        'map_html': map_html,
        'hide_input_box': hide_input_box,
        'ports': ports,
    }

    return render(request, 'debug.html', context)