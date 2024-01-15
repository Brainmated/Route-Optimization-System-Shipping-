from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm
from .pathing import Pathing, GridMap
from django.contrib.auth.views import LoginView, LogoutView
from .utils import get_ports_from_csv
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
import folium
import random
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

        # Create a Pathing instance and generate the map
        path = Pathing(location1, location2, grid_map)
        folium_map = path.get_map()
    else:
        # Default map centered at an initial location
        folium_map = folium.Map(location=[0, 0], zoom_start=5)

    # Pass the map to the template
    map_html = folium_map._repr_html_()
    context = {
        'map': map_html,
        'ports': ports,
    }
    return render(request, 'map.html', context)



def debug_view(request):
    # Define the grid size and the bounds of the grid
    grid_size = 1
    min_lat, max_lat = -10, 10
    min_lon, max_lon = -10, 10

    # Create a map object centered on the midpoint of the grid bounds with an appropriate zoom level
    m = folium.Map(location=[(min_lat + max_lat) / 2, (min_lon + max_lon) / 2], zoom_start=2, min_zoom=2)

    # Create horizontal lines (latitude lines) within the bounds
    for lat in range(min_lat, max_lat + grid_size, grid_size):
        folium.PolyLine([(lat, min_lon), (lat, max_lon)], color="black", weight=0.1).add_to(m)

    # Create vertical lines (longitude lines) within the bounds
    for lon in range(min_lon, max_lon + grid_size, grid_size):
        folium.PolyLine([(min_lat, lon), (max_lat, lon)], color="black", weight=0.1).add_to(m)

    # Emphasize the boundaries of the grid
    folium.PolyLine([(min_lat, min_lon), (min_lat, max_lon), (max_lat, max_lon), (max_lat, min_lon), (min_lat, min_lon)], color="red", weight=2).add_to(m)

    # Set the bounds of the map to the grid area
    m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    # Render map to HTML
    map_html = m._repr_html_()

    context = {
        'map_html': map_html,
    }

    return render(request, 'debug.html', context)