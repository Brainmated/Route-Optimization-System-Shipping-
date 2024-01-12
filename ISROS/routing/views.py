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
        folium_map = folium.Map(location=[45.5236, -122.6750], zoom_start=5)

    # Pass the map to the template
    map_html = folium_map._repr_html_()
    context = {
        'map': map_html,
        'ports': ports,
    }
    return render(request, 'map.html', context)



def debug_view(request):
    # Create a map object centered on a geographic midpoint (e.g., 0,0) with a starting zoom level
    m = folium.Map(location=[0, 0], zoom_start=1, min_zoom=1)

    # Define the size of the grid cells
    grid_size = 1  # Example for a 1-degree grid; adjust as needed for smaller cells

    # Add a grid to the map
    # Create horizontal lines (latitude lines)
    for lat in range(-90, 90, grid_size):
        folium.PolyLine([(lat, -180), (lat, 180)], color="black", weight=0.1).add_to(m)

    # Create vertical lines (longitude lines)
    for lon in range(-180, 180, grid_size):
        folium.PolyLine([(-90, lon), (90, lon)], color="black", weight=0.1).add_to(m)

    # Generate two distinct random grid cell positions
    random_lat1 = random.randint(-90, 90 - grid_size)
    random_lon1 = random.randint(-180, 180 - grid_size)
    random_lat2 = random.randint(-90, 90 - grid_size)
    random_lon2 = random.randint(-180, 180 - grid_size)

    # Normalize the random latitude and longitude to fit the grid
    random_lat1 = random_lat1 - random_lat1 % grid_size
    random_lon1 = random_lon1 - random_lon1 % grid_size
    random_lat2 = random_lat2 - random_lat2 % grid_size
    random_lon2 = random_lon2 - random_lon2 % grid_size

    # Ensure the second position is different from the first
    while random_lat1 == random_lat2 and random_lon1 == random_lon2:
        random_lat2 = random.randint(-90, 90 - grid_size)
        random_lon2 = random.randint(-180, 180 - grid_size)
        random_lat2 = random_lat2 - random_lat2 % grid_size
        random_lon2 = random_lon2 - random_lon2 % grid_size

    # Define the grid for pathfinding
    grid_matrix = [[1 for _ in range(360//grid_size)] for _ in range(180//grid_size)]
    grid = Grid(matrix=grid_matrix)

    # Define start and end points for the A* algorithm
    start = grid.node(random_lon1 // grid_size, random_lat1 // grid_size)
    end = grid.node(random_lon2 // grid_size, random_lat2 // grid_size)

    # Initialize the A* finder
    finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
    path, _ = finder.find_path(start, end, grid)

    # Draw the path on the map
    for step in path:
        y, x = step  # Grid library uses (y, x) convention
        map_x = x * grid_size - 180  # Convert back to longitude
        map_y = y * grid_size - 90   # Convert back to latitude
        folium.CircleMarker([map_y, map_x], radius=2, color="blue").add_to(m)

    # Render map to HTML
    map_html = m._repr_html_()

    context = {
        'map_html': map_html,
    }

    return render(request, 'debug.html', context)