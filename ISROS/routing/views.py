from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm
from django.contrib.auth.views import LoginView, LogoutView
from .utils import get_ports_from_csv
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
import folium
import random
import pathing
import requests
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

def debug_view(request):
    min_lat, max_lat = -90, 90  
    min_lon, max_lon = -180, 180  

    m = folium.Map(
        location=[(max_lat + min_lat) / 2, (max_lon + min_lon) / 2],
        zoom_start=2,
        min_zoom=2,
        max_bounds=[[min_lat, min_lon], [max_lat, max_lon]],
    )
    
    bounds = [[min_lat, min_lon], [max_lat, max_lon]]
    m.fit_bounds(bounds)

    grid_size = 1  # Each grid cell corresponds to 1 degree

    # ... [Code to draw grid lines] ...

    # 2 random locations
    start_lat = random.uniform(min_lat, max_lat)
    start_lon = random.uniform(min_lon, max_lon)
    end_lat = random.uniform(min_lat, max_lat)
    end_lon = random.uniform(min_lon, max_lon)

    # Convert lat/lon to grid coordinates
    start_grid = pathing.lat_lon_to_grid(start_lat, start_lon, min_lat, min_lon, grid_size)
    end_grid = pathing.lat_lon_to_grid(end_lat, end_lon, min_lat, min_lon, grid_size)

    # Define the grid for pathfinding
    num_rows = int((max_lat - min_lat) / grid_size)
    num_cols = int((max_lon - min_lon) / grid_size)
    grid = [[True for _ in range(num_cols)] for _ in range(num_rows)]  # True indicates walkable

    # Run A* algorithm
    path = pathing.a_star_search(grid, start_grid, end_grid)

    # Convert the path back to geographic coordinates
    geo_path = [pathing.grid_to_lat_lon(point[0], point[1], min_lat, min_lon, grid_size) for point in path]

    # Draw the path on the map
    folium.PolyLine(geo_path, color="blue", weight=2.5, opacity=1).add_to(m)

    # Add markers for start and end points
    folium.Marker([start_lat, start_lon], icon=folium.Icon(color="green")).add_to(m)
    folium.Marker([end_lat, end_lon], icon=folium.Icon(color="red")).add_to(m)

    map_html = m._repr_html_()

    context = {
        'map_html': map_html,
    }

    return render(request, 'debug.html', context)