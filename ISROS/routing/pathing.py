import folium
from folium.plugins import AntPath
import shapely.geometry
from shapely.geometry import Point, LineString, MultiLineString
import os
import numpy as np
import networkx as nx
import random
import heapq
from math import radians, cos, sin, asin, sqrt
from itertools import product
import osmnx as ox
import geopandas as gpd
from .ports import parse_ports
from django.contrib import messages
from geopy.distance import great_circle
from shapely.geometry import Point, Polygon, MultiPolygon


class Node:

    def __init__(self, id, lat, lon):
        self.id = id
        self.lat = float(lat) if lat is not None else None
        self.lon = float(lon) if lon is not None else None
        self.neighbors = []
        self.distances = {}

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

'''
The GridMap class creates a node for every integer latitude/longitude
intersection and then adds edges to each node's neighbors.
With 8 possible directions of movement the add_edges() method
handles wrapping of the map so the eastern most and western most edges connect.
'''

class GridMap:

    script_dir = os.path.dirname(os.path.abspath(__file__))
    land = gpd.read_file("routing/data/geopackages/ne_10m_land.gpkg")
    coastline = gpd.read_file("routing/data/geopackages/ne_10m_coastline.gpkg")

    #current method will test for the 1° x 1° grid
    def __init__(self, distance_threshold):
        self.nodes = set()
        self.land_nodes = self.is_land()
        self.coast_nodes = self.is_coast()
        self.distance_threshold = distance_threshold
        self.grid = {}
        self.create_grid()
        self.create_edges()

    def create_grid(self):
        for node in self.land_nodes + self.coast_nodes:
            #Calculate the grid cell key as a tuple (lat_index, lon_index)
            lat_index = int(node.lat // 0.1)
            lon_index = int(node.lon // 0.1)
            grid_cell_key = (lat_index, lon_index)

            #Add the node to the gride cell
            if grid_cell_key not in self.grid:
                self.grid[grid_cell_key] = []
            self.grid[grid_cell_key].append(node)
            self.nodes.add(node)

    def create_edges(self):
        #Iterate over the grid cells
        for grid_cell_key in self.grid:
            #Get the current cell and the neighboring cells keys
            lat_index, lon_index = grid_cell_key
            neighboring_keys = product(
                [lat_index - 1, lat_index, lat_index +1],
                [lon_index -1, lon_index, lon_index +1]
            )

            #Iterate over each node in the current cell
            for node1 in self.grid[grid_cell_key]:
                #Check nodes in neighboring cells
                for neighbor_key in neighboring_keys:
                    if neighbor_key in self.grid and neighbor_key != grid_cell_key:
                        for node2 in self.grid[neighbor_key]:
                            distance = self.haversine_distance(node1.lat, node1.lon, node2.lat, node2.lon)

                            if distance <= self.distance_threshold:
                                node1.add_neighbor(node2, distance)
                                node2.add_neighbor(node1, distance)
    
    def heuristic(self, node1, node2):
        return self.haversine_distance(node1.lat, node1.lon, node2.lat, node2.lon)
    
    @staticmethod
    def is_land():
        land_areas = []
        node_id = 0
        for _, row in GridMap.land.iterrows():
            geometry = row["geometry"]
            if isinstance(geometry, Polygon):
                land_areas += [Node(node_id, *coords) for coords in geometry.exterior.coords]
                node_id += len(geometry.exterior.coords)
            elif isinstance(geometry, MultiPolygon):
                for polygon in geometry.geoms:
                    land_areas += [Node(node_id, *coords) for coords in polygon.exterior.coords]
                    node_id += len(polygon.exterior.coords)
        
        return land_areas
    
    def is_ocean():
        pass
    
    #------------------------SUCCESS-------------------------------------------------------------
    @staticmethod
    def is_coast():
        coastline = []
        node_id = 0
        for _, row in GridMap.coastline.iterrows():
            if isinstance(row["geometry"], LineString):
                coastline += [Node(node_id,y,x) for x, y in row["geometry"].coords]
                node_id +=len(row["geometry"].coords)

            elif isinstance(row["geometry"], MultiLineString):
                for line in row["geometry"].geoms:
                    coastline += [Node(node_id,y,x) for x, y in line.coords]
                    node_id +=len(line.coords)
        return coastline
    
    def get_closest_node(self, lat, lon):
        closest_node = None
        min_distance = float("inf")
        for node in self.nodes:
            distance = self.calculate_distance(node, lat, lon)

            if distance < min_distance:
                min_distance = distance
                closest_node = node
        return closest_node

    def calculate_distance(self, node, lat2, lon2):

        R = 6361.0 #Earth radius in kilometers

        #Convert latitude and longitude from degrees to radians
        lat1, lon1 = map(radians, [node.lat, node.lon])
        lat2, lon2 = map(radians, [lat2, lon2])

        #Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        #Distance in kilometers
        distance = R * c
        return distance
    
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
    
    def a_star(self, request, start_node, goal_node):

        open_set = []
        ports = parse_ports()
        heapq.heappush(open_set, (0, start_node))

        # Extract location A and B from the POST data
        loc_a_name = request.POST.get("locationA")
        loc_b_name = request.POST.get("locationB")
        loc_a = next((port for port in ports if port["name"] == loc_a_name), None)
        loc_b = next((port for port in ports if port["name"] == loc_b_name), None)
        
        if loc_a is None or loc_b is None:
            raise ValueError("One or both locations not found.")
        
        loc_a_coord = (float(loc_a['latitude']), float(loc_a['longitude']))
        loc_b_coord = (float(loc_b['latitude']), float(loc_b['longitude']))
        
        start_node = grid_map.get_closest_node(*loc_a_coord)
        goal_node = grid_map.get_closest_node(*loc_b_coord)
    
        came_from = {start_node: None}

        #Cost from start to a node
        g_score = {start_node: 0}

        #Estimated cost from start to goal through a node
        f_score = {start_node: self.grid_map.heuristic(start_node, goal_node)}

        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == goal_node:
                return self.reconstruct_path(came_from, current)
            
            for neighbor, distance in current.neighbors.items():
                tentative_g_score = g_score[current] + distance
            
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + self,heuristic(neighbor, goal_node)

                heapq.heappush(open_set, (f-f_score[neighbor], neighbor))

        #Return failure if there's no path
        return None

    def reconstruct_path(self, came_from, current):

        #Reconstruct the path from goat to start
        path = []
        while current:
            path.append(current)
            current = came_from[current]
        path.reverse() #Reverse the path from start to goal
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
        
        start_node = grid_map.get_closest_node(*loc_a_coord)
        end_node = grid_map.get_closest_node(*loc_b_coord)

        
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