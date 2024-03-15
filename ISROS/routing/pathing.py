import folium
from folium.plugins import AntPath
import shapely.geometry
from shapely.geometry import Point, LineString, MultiLineString
import os
import numpy as np
import networkx as nx
import random
import heapq
import math
from math import radians, cos, sin, asin, sqrt
from itertools import product
import osmnx as ox
import geopandas as gpd
from .ports import parse_ports
from django.contrib import messages
from geopy.distance import great_circle
from shapely.geometry import Point, Polygon, MultiPolygon

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = -90, 90, -180, 180
LAT_STEP, LON_STEP = 0.3, 0.3

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

    def __init__(self, distance_threshold):
        self.nodes = set()
        self.distance_threshold = distance_threshold
        self.grid = {}
        self.create_grid()  
        self.create_edges()  
        self.mark_land_nodes()
        self.gfd_nodes = gpd.GeoDataFrame(
            [{"geometry": Point(node.lon, node.lat), "walkable": node.walkable} for node in self.nodes]
        )
        #Create a spatial index
        self.sindex = self.gfd_nodes.sindex

    def is_point_on_land(self, point):

        possible_matches_index = list(self.land.sindex.query(point))
        if not possible_matches_index:
            return False
        possible_matches = self.land.iloc[possible_matches_index]
        return any(point.within(land_polygon) for land_polygon in possible_matches.geometry)
    
    def create_grid(self):
        for lat in np.arange(LAT_MIN, LAT_MAX, LAT_STEP):
            for lon in np.arange(LON_MIN, LON_MAX, LON_STEP):
                point = Point(lon, lat)
                if not self.is_point_on_land(point):
                    node = Node(lat, lon, walkable=True)
                    self.nodes.add(node)
                    lat_index = int(lat / LAT_STEP)
                    lon_index = int(lon / LON_STEP)
                    grid_cell_key = (lat_index, lon_index)

                if grid_cell_key not in self.grid:
                    self.grid[grid_cell_key] = []
                self.grid[grid_cell_key].append(node)
    
    def mark_land_nodes(self):
        for node in self.nodes:
            point = Point(node.lon, node.lat)
            if self.is_point_on_land(point):
                node.walkable = False

    def create_edges(self):
        # Iterate over the nodes rather than the grid cells
        for node1 in self.nodes:
            for node2 in self.nodes:
                if node1 != node2:
                    distance = self.calculate_distance(node1.lat, node1.lon, node2.lat, node2.lon)
                    if distance <= self.distance_threshold and node2.walkable:
                        node1.add_neighbor(node2, distance)

    @staticmethod
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

        # Query the spatial index for the nearest point
        possible_matches_index = list(self.sindex.nearest(target_point.bounds, 1))
        possible_matches = self.gdf_nodes.iloc[possible_matches_index]

        # Filter out non-walkable nodes
        possible_matches = possible_matches[possible_matches['walkable']]

        if not possible_matches.empty:
            # If there are walkable nodes, return the closest one
            closest_node_data = possible_matches.iloc[0]
            closest_node = Node(closest_node_data.geometry.y, closest_node_data.geometry.x, walkable=True)
            return closest_node
        else:
            # If there are no walkable nodes, return None
            return None

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
    
'''
class Map_Marking:

    #check validity of shape files
    def __init__(self, land_shp, water_shp):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.land_data = gpd.read_file("routing/data/ne_10m_land.shp")
        self.coastline_data = gpd.read_file("routing/data/ne_10m_coastline.shp")


    #---------------------------------THE SHP FILES ARE VALID----------------------------------
    #---------------------------------CHECK WHY THE RANDOM POSITIONS ARENT THAT RANDOM---------
'''

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
        
    def dijkstra(self, request, grid_map):

        land_data = grid_map.land_nodes()
        grid_map.init_land(land_data)
        coastline_data = Pathing.is_coast()
        max_gap_distance = 0.5
        connected_coastline = Pathing.connect_coastline_gaps(coastline_data, max_gap_distance)
        grid_map.init_coastline(coastline_data)
        

        loc_a_name = request.POST.get("locationA")
        loc_b_name = request.POST.get("locationB")
        
        ports = parse_ports() 
        
        loc_a = next((port for port in ports if port["name"] == loc_a_name), None)
        loc_b = next((port for port in ports if port["name"] == loc_b_name), None)
        
        if loc_a is None or loc_b is None:
            raise ValueError("One or both locations not found.")
        
        loc_a_coord = (float(loc_a['latitude']), float(loc_a['longitude']))
        loc_b_coord = (float(loc_b['latitude']), float(loc_b['longitude']))
        
        start_node = grid_map.get_nearest_walkable_node(*loc_a_coord)
        end_node = grid_map.get_nearest_walkable_node(*loc_b_coord)

        
        queue = []
        heapq.heappush(queue, (0, start_node))
        distances = {node: float("infinity") for node in grid_map.nodes.values()}
        previous_nodes = {node: None for node in grid_map.nodes.values()}
        distances[start_node] = 0

        output_directory = r"E:/Programming in Python/applications/Thesis/ISROS/routing/data/path_classification"
        os.makedirs(output_directory, exist_ok=True)
        file_path = os.path.join(output_directory, f"path_classification_{loc_a_name}_to_{loc_b_name}.txt")

        with open(file_path, "w") as file:
            while queue:
                current_distance, current_node = heapq.heappop(queue)

                #DEBUGGING------------------------------------------------------------------------------------------------------
                if grid_map.is_land_node(current_node):
                    file.write(f"Node {current_node.id} is land\n")
                elif grid_map.is_coastal_node(current_node):
                    file.write(f"Node {current_node.id} is coastal\n")
                else:
                    file.write(f"Node {current_node.id} is ocean\n")

                if current_node == end_node:
                    break
                for neighbor in current_node.neighbors:
                    if grid_map.is_land_node(neighbor) or grid_map.is_coastal_node(neighbor):
                        continue
                    
                    distance = current_distance + grid_map.calculate_distance(current_node, neighbor)

                    if distance < distances[neighbor]:
                        distances[neighbor] = distance
                        previous_nodes[neighbor] = current_node
                        heapq.heappush(queue, (distance, neighbor))

            #reconstruct the path
            path = []
            current_node = end_node
            while current_node:
                path.insert(0, current_node)
                current_node = previous_nodes[current_node]

            file.write("Path from start to end:\n")
            for node in path:
                file.write(f"{node.id}\n")
            
        return path if path and path[0] == start_node else []
    
    def visibility_graph():
        pass
