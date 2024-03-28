from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse
from .forms import SignUpForm
from .pathing import a_star, dijkstra
from django.contrib.auth.views import LoginView, LogoutView
from .utils import get_ports_from_csv
import folium
import os
import random
import requests
import json
from .ports import parse_ports
from .graph_update import generate_or_load_graph, write_isolated_nodes_to_file, file_path, graph_file_path
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
            return redirect('debug')
        
        else:
            return render(request, "login.html", {'error_message': 'Invalid user credentials.'})
    return render(request, 'login.html')
        

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


    # Extract location A and B from the POST data
    loc_a_name = request.POST.get("locationA")
    loc_b_name = request.POST.get("locationB")
    
    ports = parse_ports()
    loc_a = next((port for port in ports if port["name"] == loc_a_name), None)
    loc_b = next((port for port in ports if port["name"] == loc_b_name), None)
    
    if loc_a is None or loc_b is None:
        return JsonResponse({"error": "One or both locations not found."}, status=400)

    start_node = (float(loc_a['longitude']), float(loc_a['latitude']))
    goal_node = (float(loc_b['longitude']), float(loc_b['latitude']))

    # Check if start_node and goal_node are returned correctly
    if start_node is None:
        return JsonResponse({"error": "Start location is not walkable or not found."}, status=400)

    if goal_node is None:
        return JsonResponse({"error": "Goal location is not walkable or not found."}, status=400)


    try:
        a_star_path = a_star(G, start_node, goal_node)
        folium.PolyLine(a_star_path, color="green", weight=2, opacity=1).add_to(m)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


    # Serialize the map to HTML
    map_html = m._repr_html_()

    context = {
        "map_html": map_html,
        "simulation_run": True,
        "distance_km": "Test",
        "locationA": request.POST.get("locationA"),
        "locationB": request.POST.get("locationB"),
    }

    # Pass the new map to the template
    return render(request, 'debug.html', context)

def blocks_view(request):
    # Load your graph, this assumes your generate_or_load_graph returns a graph object
    G = generate_or_load_graph(file_path, graph_file_path)
    
    # Get the block data
    block_counts = write_isolated_nodes_to_file(G)

    m = folium.Map(location=[0, 0], zoom_start=13)

    # Use block_counts to draw rectangles on the map
    for block, count in block_counts.items():
        if count > 0:  # Only draw blocks with isolated nodes
            lat_start, lon_start = block
            lat_end = lat_start + 1  # Adjust based on your block size
            lon_end = lon_start + 1  # Adjust based on your block size

            # Define the block bounds
            bounds = [[lat_start, lon_start], [lat_end, lon_end]]

            # Create a rectangle for the block
            folium.Rectangle(
                bounds,
                popup=f"Isolated Nodes: {count}",
                color='#ff7800',
                fill=True,
                fill_color='#ffff00',
                fill_opacity=0.2
            ).add_to(m)
            
    block_counts = write_isolated_nodes_to_file(G, write_to_file=False)
    # Render the map as HTML
    map_html = m._repr_html_()

    # Pass the map HTML to the template
    context = {'map': map_html}
    return render(request, 'blocks.html', context)

def ships_view(request):
    if request.method == "POST":
        selected_ship = request.POST.get("ship")

    return render(request, "ships.html")
