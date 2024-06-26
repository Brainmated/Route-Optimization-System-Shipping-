import pickle
import math
import os
import gc
import random
import numpy as np
from collections import defaultdict
import pandas as pd
import networkx as nx
from queue import PriorityQueue
from scipy.spatial import cKDTree
from datetime import datetime, timedelta
from .ships import Ship, ContainerCargoShip, CrudeOilTankerShip, RoRoShip
from .graph_update import generate_or_load_graph
#from graph_update import generate_or_load_graph

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
        path = nx.astar_path(graph, start, goal, heuristic=haversine, weight='weight')
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

def dijkstra_pathing(graph, start, goal, radius=50.0):
    log_to_file("Dijkstra pathfinding called")
    
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

    # Attempt to find the Dijkstra path
    try:
        path = nx.dijkstra_path(graph, start, goal)
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
    
def write_path_to_file(path, path_file_name):
    with open(path_file_name, 'w') as file:
        for node in path:
            file.write(f"{node[0]},{node[1]}\n")

def calculate_distance(path):
    total_distance = 0
    for i in range(len(path) - 1):
        distance = haversine(path[i], path[i+1])
        total_distance += distance
    distance_str = "{:.2f}".format(total_distance)
    log_to_file(f"Total distance: {distance_str} km")
    return distance_str
''' TRAVEL TIME AND ARRIVAL TIME:-------------------------------------------------------------'''

G, weather_nodes = generate_or_load_graph(file_path, graph_file_path)
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
