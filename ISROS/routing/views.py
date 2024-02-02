from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm
from .pathing import Pathing, GridMap, Map_Marking
from django.contrib.auth.views import LoginView, LogoutView
from .utils import get_ports_from_csv
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
import folium
import random
import requests
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import numpy as np

# Home page view
def index(request):
    return render(request, 'index.html')

# Login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user:
                login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

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

def show_map(request):
    min_x, min_y = (30.0, -120.0)
    max_x, max_y = (50.0, -70.0) 
    # Check if the form has been submitted
    csv_filepath = 'E:/Programming in Python/applications/Thesis/ISROS/routing/data/ports.csv'
    ports = get_ports_from_csv(csv_filepath)
    grid_map = GridMap(bounds=((min_x, min_y), (max_x, max_y)), resolution=5)

    if request.method == 'POST':
        # Get locations from the POST request
        location1 = [float(coord) for coord in request.POST['location1'].split(',')]
        location2 = [float(coord) for coord in request.POST['location2'].split(',')]

        folium_map = folium.Map(location=[0, 0], zoom_start=5)

    # Pass the map to the template
    map_html = folium_map._repr_html_()
    context = {
        'map': map_html,
        'ports': ports,
    }
    return render(request, 'map.html', context)

@require_http_methods(["POST"])
def simulate(request):
    # Parse the body of the POST request
    data = json.loads(request.body)

    # Simulate and process data here
    # ...

    # Returning a JsonResponse won't cause a page reload, so this won't hide the input-box.
    # Instead, you should render the template with a flag to hide the input-box.
    context = {
        'hide_input_box': True,
        # ... include other necessary context variables
    }
    return render(request, 'your_template.html', context)

def debug_view(request):
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

    #Randoms from Map_Marking class
    map_marker = Map_Marking("E:/Programming in Python/applications/Thesis/ISROS/routing/data/ne_10m_land.shp", 
                             "E:/Programming in Python/applications/Thesis/ISROS/routing/data/ne_10m_ocean.shp")
    map_marker.mark_points(m)
    map_marker.print_column_headers()

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

    # Generate two random locations and draw a line between them
    random_points = []
    feature_collection = {"type": "FeatureCollection", "features": []}
    for _ in range(2):
        random_lat = random.uniform(-90, 90)
        random_lon = random.uniform(-180, 180)
        random_points.append((random_lat, random_lon))  # Append the point to the list
        folium.Marker([random_lat, random_lon]).add_to(m)  # Create a marker for the random location
    
    # Draw a line between the two random points
    folium.PolyLine(random_points, color="blue", weight=2.5, opacity=0.8).add_to(m)

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
    
    # Render map to HTML
    map_html = m._repr_html_()

    context = {
        'map_html': map_html,
    }

    return render(request, 'debug.html', context)