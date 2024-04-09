from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse
from .forms import SignUpForm
from .pathing import a_star_pathing, G, weather_nodes, calculate_distance
from .ships import ContainerCargoShip, CrudeOilTankerShip, RoRoShip
from django.contrib.auth.views import LoginView, LogoutView
from .utils import get_ports_from_csv
import folium
import os
from .ports import parse_ports

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import numpy as np

def debug_view(request):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_filepath = os.path.join(script_dir, "data", "ports.csv")
    
    ports = parse_ports()

    hide_input_box = request.session.pop('hide_input_box', False)

    min_lat, max_lat = -90, 90  
    min_lon, max_lon = -180, 180  
    
    # Create a map object centered on the geographic midpoint with a starting zoom level
    #Always Mercator Projection
    m = folium.Map(
        location=[(max_lat + min_lat) / 2, (max_lon + min_lon) / 2],
        zoom_start=3,
        min_zoom=3,
        tiles="Cartodb Positron",
        max_bounds=[[min_lat, min_lon], [max_lat, max_lon]],  # This will restrict the view to the map's initial bounds
    )

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

    ship_type = request.POST.get("shipType")
    ship_types = {
        "container": ContainerCargoShip,
        "tanker": CrudeOilTankerShip,
        "roro": RoRoShip,
    }
    # Retrieve cargo weight, propeller condition, and current gas price from POST data
    cargo_weight_percentage = float(request.POST.get("weight", 50))  # Default to 50 if not provided
    propeller_condition = float(request.POST.get("propellerCondition", 1.0))  # Default to 1 if not provided
    current_gas_price = float(request.POST.get("currentGasPrice", 0))  # Default to 0 if not provided

    ship_class = ship_types.get(ship_type)
    if ship_class is None:
        return JsonResponse({"error": "Invalid ship type selected."}, status=400)
    
    ship = ship_class(propeller_condition_factor=propeller_condition)

    # Calculate the adjusted speed, fuel consumption, and cost
    adjusted_speed_knots = ship.get_adjusted_speed_knots(cargo_weight_percentage)
    adjusted_speed_kmh = ship.get_adjusted_speed_kmh(cargo_weight_percentage)
    fuel_consumption_per_hour = ship.get_fuel_consumption_per_hour(cargo_weight_percentage)
    fuel_cost_per_nautical_mile = ship.get_fuel_cost_per_nautical_mile(cargo_weight_percentage, current_gas_price)

    start_node = (float(loc_a['latitude']), float(loc_a['longitude']))
    goal_node = (float(loc_b['latitude']), float(loc_b['longitude']))

    # Check if start_node and goal_node are returned correctly
    if start_node is None:
        return JsonResponse({"error": "Start location is not walkable or not found."}, status=400)

    if goal_node is None:
        return JsonResponse({"error": "Goal location is not walkable or not found."}, status=400)

    # Add markers for start and goal nodes
    start_marker = folium.Marker(
        location=[start_node[0], start_node[1]],  # folium takes coordinates in lat, lon order
        popup=f'Start: {start_node[0]}, {start_node[1]}',
        icon=folium.Icon(color='green', icon='play')
    )
    start_marker.add_to(m)
    goal_marker = folium.Marker(
        location=[goal_node[0], goal_node[1]],  # folium takes coordinates in lat, lon order
        popup=f'Goal: {goal_node[0]}, {goal_node[1]}',
        icon=folium.Icon(color='red', icon='flag')
    )
    goal_marker.add_to(m)

    # Add red transparent circles around weather nodes
    for node in weather_nodes:
        folium.Circle(
            location=node,
            radius=15000,  
            color='red',
            fill=True,
            fill_opacity=0.2
        ).add_to(m)
        
    try:
        a_star_path = a_star_pathing(G, start_node, goal_node)
        if a_star_path is None:
            raise ValueError("No path found or the start and goal nodes are not connected.")
        folium.PolyLine(a_star_path, color="green", weight=1, opacity=1).add_to(m)

        request.session['path'] = a_star_path
        distance_km = calculate_distance(a_star_path)
        
        # Ensure distance_km is a float
        distance_km = float(distance_km)
        
        # Ensure ship.average_speed_knots is a float
        average_speed_knots = float(ship.average_speed_knots)
        
        travel_time_hours = distance_km / (average_speed_knots * 1.852)
        fuel_consumption = travel_time_hours * ship.fuel_consumption_rate
        travel_time_hours_rounded = round(travel_time_hours, 3)
        fuel_consumption_rounded = round(fuel_consumption, 3)

        # Calculate the total fuel consumption and cost for the given distance
        total_fuel_consumption = fuel_consumption_per_hour * (distance_km / adjusted_speed_knots)
        total_fuel_cost = fuel_cost_per_nautical_mile * distance_km

    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # Serialize the map to HTML
    map_html = m._repr_html_()

    context = {
        "map_html": map_html,
        "simulation_run": True,
        "distance_km": distance_km,
        "locationA": request.POST.get("locationA"),
        "locationB": request.POST.get("locationB"),
        "selected_ship": ship_type,
        "average_speed_knots": ship.average_speed_knots,
        "adjusted_speed_kmh": round(adjusted_speed_kmh, 3),
        "fuel_consumption_per_hour": fuel_consumption_per_hour,
        "fuel_cost_per_nautical_mile": round(fuel_cost_per_nautical_mile, 3),
        "total_fuel_consumption": round(total_fuel_consumption, 3),
        "total_fuel_cost": round(total_fuel_cost, 3),
        "fuel_consumption_rate": ship.fuel_consumption_rate,
        "travel_time_hours": travel_time_hours_rounded,
        "fuel_consumption": fuel_consumption_rounded,
    }

    return render(request, 'debug.html', context)

def export_path(request):
    path = request.session.get('path')
    if path is None:
        return HttpResponse("No path to export.", status=404)
    
    response = HttpResponse(content_type="text/plain")
    response['Content-Disposition'] = 'attachment; filename="path.txt"'

    for node in path:
        response.write(f"{node[0]},{node[1]}\n")
    
    del request.session['path']

    return response
'''
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
'''
