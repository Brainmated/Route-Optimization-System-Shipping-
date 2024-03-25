import pickle
import math
import os
import gc
import numpy as np
import pandas as pd
import networkx as nx
from queue import PriorityQueue
from scipy.spatial import cKDTree
from datetime import datetime, timedelta
from graph_update import generate_or_load_graph

def debug_print(message):
    print(f"DEBUG: {message}")

script_dir = os.path.dirname(os.path.abspath(__file__))
debug_print(f"Script directory: {script_dir}")

file_path = os.path.join(script_dir, 'grid_map', 'sea_grid.pkl')
graph_file_path = os.path.join(script_dir, 'grid_map', 'sea_graph.pkl')
debug_print(f"Grid file path: {file_path}")
path_print = os.path.join(script_dir, 'data')


# Haversine formula to calculate the distance between two points on the Earth's surface
def haversine(coord1, coord2):
    R = 6371  # Earth radius in kilometers
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance

def find_nearest_navigable_node_within_radius(graph, point, radius=50.0):
    # Extract the navigable nodes from the graph
    navigable_nodes = [tuple(node) for node in graph.nodes]

    if len(navigable_nodes) == 0:  # Corrected line
        raise ValueError("There are no navigable nodes in the graph to find the closest point to.")
    # Initialize the closest node and its distance
    closest_node = None
    closest_dist = float('inf')

    # Iterate over all nodes to find the nearest navigable node
    for node in navigable_nodes:
        distance = haversine(point, node)
        if distance < closest_dist and distance <= radius:
            closest_dist = distance
            closest_node = node

    if closest_node is not None:
        return closest_node
    else:
        error_message = f"No navigable nodes within a radius of {radius} km from point {point}."
        raise ValueError(error_message)

# A* algorithm
def a_star(graph, start, goal):
    try:
        start = find_nearest_navigable_node_within_radius(graph, start)
        goal = find_nearest_navigable_node_within_radius(graph, goal)
    except ValueError as e:
        print(f"Error finding start or goal: {e}")
        return None

    if start not in graph.nodes or goal not in graph.nodes:
        print("Start or goal node is not in the graph.")
        return None

    if start == goal:
        print("Start and goal nodes are the same; no path needed.")
        return [start]

    frontier = PriorityQueue()
    frontier.put((0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while not frontier.empty():
        current = frontier.get()[1]

        print(f"Current node: {current}")  # Debug current node
        if current == goal:
            print("Goal reached.")
            break

        for neighbor in graph.neighbors(current):
            new_cost = cost_so_far[current] + haversine(current, neighbor)
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + haversine(neighbor, goal)
                frontier.put((priority, neighbor))
                came_from[neighbor] = current
                print(f"Neighbor {neighbor} added to frontier with priority {priority}.")  # Debug neighbor

    if goal in came_from:
        current = goal
        path = []
        while current != start:
            path.append(current)
            current = came_from[current]
        path.append(start)
        path.reverse()
        print(f"Path found: {path}")  # Debug final path
        return path
    else:
        print("Path not found.")
        return None

# Dijkstra's algorithm
def dijkstra(graph, start, goal):

    start = find_nearest_navigable_node_within_radius(graph, start)
    goal = find_nearest_navigable_node_within_radius(graph, goal)

    frontier = PriorityQueue()
    frontier.put((0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    
    while not frontier.empty():
        current = frontier.get()[1]
        
        if current == goal:
            break
        
        for neighbor in graph.neighbors(current):
            new_cost = cost_so_far[current] + haversine(current, neighbor)
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                frontier.put((new_cost, neighbor))
                came_from[neighbor] = current
    
    # Reconstruct path
    current = goal
    path = []
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()
    return path

def write_path_to_file(path_print, path_file_name):
    with open(path_file_name, 'w') as file:
        for node in path_file_name:
            file.write(f"{node[0]},{node[1]}\n")

'''
def calculate_travel_time(graph, path, average_speed_kmh, start_datetime):
    
    # Calculate the total distance by summing the distance between each consecutive pair of nodes
    total_distance_km = sum(haversine(path[i], path[i+1]) for i in range(len(path) - 1))
    
    # Calculate total travel time in hours
    travel_time_hours = total_distance_km / average_speed_kmh

    # Calculate the arrival datetime
    arrival_datetime = start_datetime + timedelta(hours=travel_time_hours)

    return travel_time_hours, arrival_datetime

G = generate_or_load_graph(file_path, graph_file_path)
start_coord = (40.68, -74.01)
goal_coord = (-10.26, 40.13)

debug_print(f"Starting A* algorithm from {start_coord} to {goal_coord}...")
'''
    
''' For Speed and Time:-------------------------------------------------------------
# Example usage:
average_speed_kmh = 30  # Replace with the actual average speed of the vessel
start_datetime = datetime.strptime('2024-03-21 08:00:00', '%Y-%m-%d %H:%M:%S')  # Specify the start time

# Assuming 'path' is obtained from a_star or dijkstra
travel_time, arrival_time = calculate_travel_time(G, path, average_speed_kmh, start_datetime)

debug_print(f"Expected travel time: {travel_time:.2f} hours")
debug_print(f"Estimated arrival time: {arrival_time.strftime('%Y-%m-%d %H:%M:%S')}")
'''


''' Modified Speed with weight:-------------------------------------------------------------
def calculate_modified_speed(average_speed_kmh, current_load, max_load_capacity, speed_reduction_factor):
    """
    Calculate the vessel's modified speed based on its load.

    :param average_speed_kmh: The vessel's average speed when not loaded in kilometers per hour.
    :param current_load: The current load of the vessel.
    :param max_load_capacity: The maximum load capacity of the vessel.
    :param speed_reduction_factor: The reduction factor of the speed per percentage of load.
    :return: The modified speed of the vessel in kilometers per hour.
    """
    if current_load > max_load_capacity:
        raise ValueError("The current load cannot exceed the maximum load capacity.")

    # Calculate the percentage of the current load
    load_percentage = current_load / max_load_capacity

    # Calculate the speed reduction based on the load
    speed_reduction = average_speed_kmh * speed_reduction_factor * load_percentage

    # Calculate the modified speed
    modified_speed_kmh = average_speed_kmh - speed_reduction

    return modified_speed_kmh
'''

''' Modified Fuel Cost and Consumption:-------------------------------------------------------------
def calculate_fuel_consumption_and_cost(path, fuel_efficiency, gas_price):
    """
    Calculate the total fuel consumption and cost for a given route.

    :param path: List of tuples representing the (latitude, longitude) coordinates of the route
    :param fuel_efficiency: Fuel efficiency of the ship in gallons per nautical mile
    :param gas_price: Current gas price per gallon
    :return: Tuple containing total fuel consumption in gallons and total cost
    """
    total_distance = 0
    total_fuel_consumption = 0
    total_cost = 0

    # Calculate the total distance of the path
    for i in range(len(path) - 1):
        segment_distance = haversine(path[i], path[i+1])
        total_distance += segment_distance

    # Calculate the total fuel consumption
    total_fuel_consumption = total_distance * fuel_efficiency

    # Calculate the total cost
    total_cost = total_fuel_consumption * gas_price

    return total_fuel_consumption, total_cost
'''

try:
    G = generate_or_load_graph(file_path, graph_file_path)

    # Define start and goal coordinates
    start_coord = (40.68, -74.01)  # Example: New York City
    goal_coord = (-10.26, 40.13)  

    debug_print("Finding nearest navigable start node...")
    start_node = find_nearest_navigable_node_within_radius(G, start_coord)
    debug_print(f"Start node found: {start_node}")

    debug_print("Finding nearest navigable goal node...")
    goal_node = find_nearest_navigable_node_within_radius(G, goal_coord)
    debug_print(f"Goal node found: {goal_node}")

    if start_node is None or goal_node is None:
        debug_print("Navigation issue: Start node or goal node could not be found.")
    else:
        debug_print(f"Starting A* algorithm from {start_node} to {goal_node}...")
        path = a_star(G, start_node, goal_node)
        
        if path is not None:
            debug_print("Path found:")
            for node in path:
                debug_print(node)
        else:
            debug_print("No path could be found from start to goal with the given parameters.")
except Exception as e:
    debug_print(f"An error occurred: {e}")
