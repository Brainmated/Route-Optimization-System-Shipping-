import folium
from folium.plugins import AntPath
import shapely.geometry
from shapely.geometry import Point, LineString, MultiLineString
import os
import numpy as np
import networkx as nx
import pickle
import random
import heapq
import math
from math import radians, cos, sin, asin, sqrt
from itertools import product
import osmnx as ox
import geopandas as gpd
from .ports import parse_ports
from django.contrib import messages
from sklearn.neighbors import KDTree
from geopy.distance import great_circle
from shapely.geometry import Point, Polygon, MultiPolygon
from pathlib import Path

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = -90, 90, -180, 180
LAT_STEP, LON_STEP = 1, 1

class Node:

    def __init__(self, lat, lon, id=None, walkable=False):
        self.id = id
        self.lat = float(lat) if lat is not None else None
        self.lon = float(lon) if lon is not None else None
        self.neighbors = []
        self.distances = {}
        self.walkable = walkable
    
    def __lt__(self, other):
        return self.id < other.id

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return (self.lat, self.lon) == (other.lat, other.lon)
    
    def __hash__(self):
        return hash((self.lat, self.lon))
    
    def is_valid(self):
        return self.lat is not None and self.lon is not None and -90 <= self.lat <= 90 and -180 <= self.lon <= 180
    
    def add_neighbor(self, neighbor, distance):
        self.neighbors.append(neighbor)
        self.distances[neighbor] = distance

    def __repr__(self):
        return f"Node(id= {self.id}, lat= {self.lat}, lon= {self.lon}, walkable={self.walkable})"
'''
The GridMap class creates a node for every integer latitude/longitude
intersection and then adds edges to each node's neighbors.
With 8 possible directions of movement the add_edges() method
handles wrapping of the map so the eastern most and western most edges connect.
'''

class GridMap:

    script_dir = os.path.dirname(os.path.abspath(__file__))
    land = gpd.read_file("routing/data/geopackages/ne_10m_land.gpkg")
    land_sindex = land.sindex  # Create the spatial index

    def __init__(self, distance_threshold):
        self.nodes = set()
        self.distance_threshold = distance_threshold
        self.grid = {}
        self.land_nodes = set()
        self.load_land_nodes()

    def initialize_map(self, start_node, goal_node):
        # Try to load the pre-generated grid
        if not self.load_grid():
            # If the grid does not exist, create it and save it
            self.create_grid(start_node, goal_node)
            self.create_edges()
            self.mark_land_nodes()
            self.save_grid()

    def save_grid(self):
        # Serialize the grid and nodes to a file
        filepath = Path(self.script_dir) / 'grid_map.pkl'
        with filepath.open('wb') as file:
            pickle.dump((self.grid, self.nodes), file)

        file_size = filepath.stat().st_size
        print(f"Grid map saved! File size: {file_size} bytes.")

    def load_grid(self):
        # Deserialize the grid and nodes from a file if it exists
        filepath = Path(self.script_dir) / 'grid_map.pkl'
        if filepath.exists():
            file_size = filepath.stat().st_size
            print(f"Loading grid map... Estimated file size: {file_size} bytes.")
            try:
                with filepath.open('rb') as file:
                    self.grid, self.nodes = pickle.load(file)
                print("Grid map loaded successfully!")
                return True
            except (FileNotFoundError, pickle.UnpicklingError):
                print("Failed to load grid map.")
                return False
        else:
            print("No grid map file found.")
            return False
        
    def load_land_nodes(self):
        for lat in range(LAT_MIN, LAT_MAX + 1, LAT_STEP):
            for lon in range(LON_MIN, LON_MAX + 1, LON_STEP):
                point = Point(lon, lat)
                if self.point_is_land(point):
                    self.land_nodes.add((lat, lon))

    def point_is_land(self, point):
        # Use the spatial index to find potential matches more efficiently
        possible_matches_index = list(self.land_sindex.intersection(point.bounds))
        possible_matches = self.land.iloc[possible_matches_index]

        # Check for precise matches
        precise_matches = possible_matches[possible_matches.intersects(point)]
        return not precise_matches.empty

    def create_grid(self, start_node=None, goal_node=None):
        # Calculate the total number of iterations
        lat_range = range(LAT_MIN, LAT_MAX + 1, LAT_STEP)
        lon_range = range(LON_MIN, LON_MAX + 1, LON_STEP)
        total_iterations = len(lat_range) * len(lon_range)
        iteration_count = 0

        # Iterate over the entire map
        for lat in lat_range:
            for lon in lon_range:
                iteration_count += 1

                # Calculate and print the progress percentage
                progress = (iteration_count / total_iterations) * 100
                print(f"Grid creation progress: {progress:.2f}%", end='\r')

                # Only add nodes that are not on land
                point = Point(lon, lat)
                if not self.point_is_land(point):
                    node = Node(lat, lon)  # Assuming Node class initialization is correct
                    self.nodes.add(node)
                    grid_cell_key = (lat, lon)

                    if grid_cell_key not in self.grid:
                        self.grid[grid_cell_key] = []
                    self.grid[grid_cell_key].append(node)

        print("\nGrid creation complete!")

    def create_edges(self):
        # Convert nodes to a list and construct a KDTree for efficient neighbor lookup
        nodes_list = list(self.nodes)
        kd_tree = KDTree([(node.lat, node.lon) for node in nodes_list])
        
        for node1 in self.nodes:
            # Query the KDTree for nodes within the distance threshold
            indices = kd_tree.query_radius([[node1.lat, node1.lon]], r=self.distance_threshold)
            for i in indices[0]:
                node2 = nodes_list[i]
                if node1 != node2 and node2.walkable:
                    distance = self.calculate_distance(node1.lat, node1.lon, node2.lat, node2.lon)
                    node1.add_neighbor(node2, distance)

    def is_land():
        land_nodes = []
        node_id = 0
        # Iterate through the land GeoDataFrame "geometry" column
        for _, row in GridMap.land.iterrows():
            geometry = row["geometry"]
            if isinstance(geometry, Polygon):
                for coords in geometry.exterior.coords:
                    # Swap coords[1] and coords[0] to match lat, lon order
                    land_nodes.append(Node(coords[1], coords[0], node_id, walkable=False))
                    node_id += 1
            elif isinstance(geometry, MultiPolygon):
                for polygon in geometry.geoms:
                    for coords in polygon.exterior.coords:
                        # Swap coords[1] and coords[0] to match lat, lon order
                        land_nodes.append(Node(coords[1], coords[0], node_id, walkable=False))
                        node_id += 1
        # Optionally, log the count of generated non-walkable land nodes
        print(f"Generated non-walkable land nodes: {len(land_nodes)}")
        return land_nodes
    
    def get_nearest_walkable_node(self, target_lat, target_lon):
        # Create a point from the target coordinates
        target_point = Point(target_lon, target_lat)

        # Initialize variables to keep track of the closest walkable node and its distance
        closest_node = None
        closest_distance = float('inf')

        # Iterate through all nodes to find the nearest walkable node
        for node in self.nodes:  # Assuming self.nodes is an iterable of Node objects
            if (node.lat, node.lon) not in self.land_nodes:
                # Calculate the distance between the target point and the current node
                node_point = Point(node.lon, node.lat)
                distance = target_point.distance(node_point)  # Ensure distance is calculated appropriately

                # Update the closest walkable node and its distance if this node is closer
                if distance < closest_distance:
                    closest_node = node
                    closest_distance = distance

        # Return the closest walkable node or None if no walkable node is found
        return closest_node

    def calculate_distance(self, lat1, lon1, lat2, lon2):

        R = 6361.0 #Earth radius in kilometers

        #Convert latitude and longitude from degrees to radians
        lat1, lon1 = map(radians, [lat1, lon1])
        lat2, lon2 = map(radians, [lat2, lon2])

        #Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        #Distance in kilometers
        distance = R * c
        return distance
    
    def heuristic(self, node1, node2):
        # Use the haversine() method to estimate the distance between node1 and node2.
        return self.calculate_distance(node1.lat, node1.lon, node2.lat, node2.lon)
    

class Map_Marking:
    @staticmethod
    def mark_grid_on_map(m, grid_map, grid_size):
        # Create horizontal lines (latitude lines)
        for lat in range(-90, 90, grid_size):
            folium.PolyLine([(lat, -180), (lat, 180)], color="blue", weight=0.1).add_to(m)

        # Create vertical lines (longitude lines)
        for lon in range(-180, 180, grid_size):
            folium.PolyLine([(-90, lon), (90, lon)], color="blue", weight=0.1).add_to(m)

        # Mark all the nodes on the map
        for node in grid_map.nodes:
            folium.CircleMarker(
                location=[node.lat, node.lon],
                radius=1,
                color='green' if node.walkable else 'red',
                fill=True,
                fill_opacity=0.7
            ).add_to(m)

        # Optionally, draw edges as well (commented out by default for performance reasons)
        # for node in grid_map.nodes:
        #     for neighbor in node.neighbors:
        #         folium.PolyLine(
        #             locations=[(node.lat, node.lon), (neighbor.lat, neighbor.lon)],
        #             weight=1,
        #             color='green'
        #         ).add_to(m)

        return m

class Pathing:

    def __init__(self, grid_map):

        self.grid_map = grid_map

    def a_star(self, start_node, goal_node):

        #Check the start and end nodes for walkability
        if not (start_node.walkable and goal_node.walkable):
            logger.error("Start or goal node is not walkable.")
            raise ValueError("Start or goal node is not walkable.")
        
        # Ensure the start and end nodes are positioned correctly
        if not (start_node.is_valid() and goal_node.is_valid()):
            logger.error("Start or goal node has invalid positioning.")
            raise ValueError("Start or goal node has invalid positioning.")

        logger.info("Starting A* with start node: %s and goal node: %s", start_node, goal_node)

        open_set = []
        closed_set = set()  # To track nodes already visited or in open_set

        heapq.heappush(open_set, (0, start_node))
        came_from = {start_node: None}

        # Cost from start to a node
        g_score = {start_node: 0}

        # Estimated cost from start to goal through a node
        f_score = {start_node: self.grid_map.heuristic(start_node, goal_node)}

        while open_set:
            current = heapq.heappop(open_set)[1]
            logger.debug(f"Current node: {current}")
            logger.debug(f"Open set: {[n.id for _, n in open_set]}")
            logger.debug(f"Closed set: {[n.id for n in closed_set]}")
            logger.debug(f"Came from: {came_from}")

            if current in closed_set:
                continue  # Skip processing this node if it's already been visited

            if current == goal_node:
                path = self.reconstruct_path(came_from, current)
                logger.info("Path found: %s", path)
                return path
            
            closed_set.add(current)  # Add the current node to the closed_set

            for neighbor in current.neighbors:
                distance = current.distances[neighbor]

                if not neighbor.walkable or neighbor in closed_set:
                    continue  # Ignore the neighbor which is not walkable or already evaluated

                tentative_g_score = g_score[current] + distance
            
                if neighbor not in g_score or tentative_g_score < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.grid_map.heuristic(neighbor, goal_node)

                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
                    logger.debug(f"Setting predecessor of {neighbor} to {current}")

                    # Only push the neighbor to the heap if it's not there already
                    if neighbor not in open_set:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))

        logger.warning("Failed to find a path from start to goal.")
        # Return failure if there's no path
        return None

    def reconstruct_path(self, came_from, current):
        # Reconstruct the path from goal to start by walking backwards from the goal
        path = []
        while current:
            path.append(current)
            current = came_from[current]
        path.reverse()  # Reverse the path from start to goal
        logger.debug("Reconstructed path: %s", path)
        return path
    
    @staticmethod
    def straight_path(request, map_obj):
        # Extract location A and B from the POST data
        loc_a_name = request.POST.get("locationA")
        loc_b_name = request.POST.get("locationB")
        ports = parse_ports() 

        loc_a = next((port for port in ports if port["name"] == loc_a_name), None)
        loc_b = next((port for port in ports if port["name"] == loc_b_name), None)

        loc_a_coord = (float(loc_a['latitude']), float(loc_a['longitude']))
        loc_b_coord = (float(loc_b['latitude']), float(loc_b['longitude']))

        #Input validation
        if loc_a is None or loc_b is None:
            messages.error(request, "One or both locations not found.")
            
            return map_obj  # Return the map object without changes

        # Draw the path from loc_a to loc_b
        folium.PolyLine(
            [(float(loc_a['latitude']), float(loc_a['longitude'])), (float(loc_b['latitude']), float(loc_b['longitude']))],
            color="red",
            weight=2.5,
            opacity=1
        ).add_to(map_obj)

        # Update the map's location to center between loc_a and loc_b
        map_obj.location = [
            (float(loc_a['latitude']) + float(loc_b['latitude'])) / 2,
            (float(loc_a['longitude']) + float(loc_b['longitude'])) / 2
        ]
        distance_km = great_circle(loc_a_coord, loc_b_coord).kilometers
        formatted_distance = f"{distance_km:.3f}"

        return map_obj, formatted_distance

    def get_path_coordinates():
        pass

    def get_restrictions():
        #https://github.com/genthalili/searoute-py/issues/25
        pass
    '''
    Here is some output that might help while debugging:
    create_nodes() triggered
    Debugging: Starting A* algorithm
    start_coords = {'name': 'Wolfe Island', 'latitude': '44.2', 'longitude': '-76.433333'}
    goald_coords = {'name': 'Charlestown', 'latitude': '50.333333', 'longitude': '-4.75'}
    Initial node set, None
    End node set, None
    Figure what's wrong this time.
    ''' 

    def validate_coordinates(lat, lon):
        if not -90 <= lat <= 90:
            raise ValueError(f"Latitude {lat} is out of bounds. Must be between -90 and 90.")
        if not -180 <= lon <= 180:
            raise ValueError(f"Longitude {lon} is out of bounds. Must be between -180 and 180.")
    
    def visibility_graph():
        pass
