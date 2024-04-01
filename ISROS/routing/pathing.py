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
from .graph_update import generate_or_load_graph

def debug_print(message):
    print(f"DEBUG: {message}")

script_dir = os.path.dirname(os.path.abspath(__file__))
debug_print(f"Script directory: {script_dir}")

file_path = os.path.join(script_dir, 'grid_map', 'sea_grid.pkl')
graph_file_path = os.path.join(script_dir, 'grid_map', 'sea_graph.pkl')
debug_print(f"Grid file path: {file_path}")
path_print = os.path.join(script_dir, 'data')

def find_isolated_nodes(graph):
    isolated = list(nx.isolates(graph))
    return isolated

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
    navigable_nodes = [node for node in graph.nodes]

    if len(navigable_nodes) == 0:
        raise ValueError("There are no navigable nodes in the graph to find the closest point to.")
    
    # Create the KD-tree from the navigable nodes
    tree = cKDTree(navigable_nodes)
    
    # Find the indices of all points within the specified radius
    indices = tree.query_ball_point(point, radius)

    if len(indices) == 0:  # No points found within the radius
        error_message = f"No navigable nodes within a radius of {radius} km from point {point}."
        raise ValueError(error_message)
    
    # Find the nearest node within the indices
    nearest_index = tree.query(point, k=1, distance_upper_bound=radius)[1]
    if nearest_index == len(navigable_nodes):
        error_message = f"No navigable nodes within a radius of {radius} km from point {point}."
        raise ValueError(error_message)

    # Return the nearest navigable node
    return navigable_nodes[nearest_index]

def log_to_file(message, file_name="debug_log.txt"):
    with open(file_name, 'a') as f:
        f.write(message + "\n")

def a_star_pathing(graph, start, goal, radius=50.0):
    log_to_file("A* pathfinding called")
    
    # Check if the start and goal nodes are navigable, if not find the nearest navigable nodes
    if start not in graph:
        try:
            start = find_nearest_navigable_node_within_radius(graph, start, radius)
            log_to_file(f"Changed start node to nearest navigable node: {start}")
        except ValueError as e:
            log_to_file(str(e))
            return None

    if goal not in graph:
        try:
            goal = find_nearest_navigable_node_within_radius(graph, goal, radius)
            log_to_file(f"Changed goal node to nearest navigable node: {goal}")
        except ValueError as e:
            log_to_file(str(e))
            return None

    if not nx.has_path(graph, start, goal):
        log_to_file("Start and goal are not connected in the graph.")
        return None

    # Attempt to find the A* path
    try:
        path = nx.astar_path(graph, start, goal, heuristic=haversine)
        log_to_file("Path found:")
        for node in path:
            log_to_file(str(node))
        return path
    except nx.NetworkXNoPath:
        log_to_file("No path exists between the provided start and goal nodes.")
        return None
    except nx.NodeNotFound as e:
        log_to_file(str(e))
        return None

# Dijkstra's algorithm
def dijkstra(graph, start, goal, debug_file="dijkstra_debug.txt"):
    try:
        # Find the nearest navigable nodes to the start and goal
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
        
        log_to_file(f"Current node: {current}", debug_file)  # Log current node to file
        
        if current == goal:
            log_to_file("Goal reached.", debug_file)
            break
        
        for neighbor in graph.neighbors(current):
            if graph.nodes[neighbor].get('navigable', True):  # Check if the neighbor is navigable
                new_cost = cost_so_far[current] + haversine(current, neighbor)
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost  # Priority is just the cost for Dijkstra
                    frontier.put((priority, neighbor))
                    came_from[neighbor] = current
                    log_to_file(f"Neighbor {neighbor} added to frontier with priority {priority}.", debug_file)  # Log neighbor

    if goal in came_from:
        # Reconstruct path
        current = goal
        path = []
        while current != start:
            path.append(current)
            current = came_from[current]
        path.append(start)
        path.reverse()
        
        print(f"Path found: {path}", debug_file)
        return path
    else:
        print("Path not found.", debug_file)
        return None

def write_path_to_file(path, path_file_name):
    with open(path_file_name, 'w') as file:
        for node in path:
            file.write(f"{node[0]},{node[1]}\n")

def calculate_distance(path):
    total_distance = 0
    for i in range(len(path) - 1):
        distance = haversine(path[i], path[i+1])
        total_distance += distance
    log_to_file(f"Total distance: {total_distance:.2f} km")

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
G = generate_or_load_graph(file_path, graph_file_path)
print(f"Graph loaded.")
'''
if __name__ == "__main__":
    try:
        G = generate_or_load_graph(file_path, graph_file_path)  # Assuming this function is defined
        debug_print(f"Graph has {len(G.nodes)} nodes and {len(G.edges)} edges")

        isolated_nodes = find_isolated_nodes(G)
        if isolated_nodes:
            log_to_file(f"Isolated nodes found: {len(isolated_nodes)}")
            # Optionally log the isolated nodes or handle them differently here
            for node in isolated_nodes:
                log_to_file(str(node))
        else:
            debug_print("No isolated nodes found in the graph.")

        # Define start and goal coordinates
        start_coord = (40.68, -74.01)  # Replace with actual start coordinates
        goal_coord = (-10.26, 40.13)   # Replace with actual goal coordinates

        log_to_file(f"Starting A* algorithm from {start_coord} to {goal_coord}...")
        path = a_star_pathing(G, start_coord, goal_coord)

        if path is not None:
            log_to_file("Path found:")
            for node in path:
                log_to_file(str(node))
            calculate_distance(path)
        else:
            log_to_file("No path could be found from start to goal with the given parameters.")
    except Exception as e:
        log_to_file(f"An error occurred: {e}")
'''
