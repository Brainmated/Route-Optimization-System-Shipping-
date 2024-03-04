import folium
from folium.plugins import AntPath
import shapely.geometry
from shapely.geometry import Point, LineString, MultiLineString
import os
import sys
import traceback
import numpy as np
import networkx as nx
import random
import heapq
from math import radians, cos, sin, asin, sqrt
import osmnx as ox
import geopandas as gpd
from .ports import parse_ports
from django.contrib import messages
from geopy.distance import great_circle
from shapely.geometry import Point, Polygon, MultiPolygon
import time


class Node:
    start_time = time.time()

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

    end_time = time.time()
    comp_time = end_time - start_time
    print(f"Nodes: {comp_time}")
'''
The GridMap class creates a node for every integer latitude/longitude
intersection and then adds edges to each node's neighbors.
With 8 possible directions of movement the add_edges() method
handles wrapping of the map so the eastern most and western most edges connect.
'''

class GridMap:
    start_time = time.time()

    #current method will test for the 1° x 1° grid
    def __init__(self, min_lat=-90, max_lat=90, min_lon=-180, max_lon=180, resolution=1.0):
        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lon = min_lon
        self.max_lon = max_lon
        self.resolution = resolution
        self.nodes = self.create_nodes()
        self.coastal_nodes = self.coastal_nodes()
        self.add_edges()

    #method that creates nodes on the grid to help map the cells
    def create_nodes(self):
        #set nodes as a dictionary and set attributes
        nodes = {}
        node_id = 0
        for lat in np.arange(self.min_lat, self.max_lat, self.resolution):
            for lon in np.arange(self.min_lon, self.max_lon, self.resolution):
                nodes[(float(lat), float(lon))] = Node(node_id, lat, lon)
                node_id += 1
        return nodes
    

    def add_edges(self):

        #8 directions for the 8 edges of every node to move on
        directions = [
            (-1, 1), (-1, 0), (-1, 1), #Southwest | South |Southeast
            (0, 1),            (0, 1),  #West | Node | East
            (1, -1), (1, 0), (1, 1),  #Northwest | North | Northeast
        ]

        for (lat, lon), node in self.nodes.items():
            for d_lat, d_lon in directions:
                neighbor_lat = lat + d_lat * self.resolution
                neighbor_lon = lon + d_lon * self.resolution

                #degree wrapping for longitude
                if neighbor_lon < -180:
                    neighbor_lon += 360
                elif neighbor_lon > 180:
                    neighbor_lon -= 360

                #degree wrapping for latitude
                if neighbor_lat < -90 or neighbor_lat > 90:
                    #just skip creating more edges that go beyond the two poles
                    continue

                neighbor = self.nodes.get((neighbor_lat, neighbor_lon))

                if neighbor:
                    distance = self.calculate_distance(node, neighbor)
                    node.add_neighbor(neighbor, distance)

    @staticmethod
    def calculate_distance(node1, node2):

        R = 6371.0

        lat1 = radians(node1.lat)
        lon1 = radians(node1.lon)
        lat2 = radians(node2.lat)
        lon2 = radians(node2.lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2*asin(sqrt(a))

        distance = R*c

        return distance
    
    def get_closest_node(self, lat, lon):
        
        grid_lat = float(round(lat/self.resolution) * self.resolution)
        grid_lon = float(round(lon/self.resolution) * self.resolution)

        #wrap longitude if necessary
        if grid_lon <= -180:
            grid_lon += 360
        elif grid_lon > 180:
            grid_lon -= 360
        return self.nodes.get((grid_lat, grid_lon))
    
    def land_nodes(self):
        land_nodes = set()
        land_areas = Pathing.is_land()

        for node in land_areas:
            if node.is_valid():
                land_nodes.add(node)

        return land_nodes
    
    def init_land(self, land_data):
        self.land_nodes = set(land_data)

    def is_land_node(self, node):
        return node in self.land_nodes
    
    def coastal_nodes(self):
        coastal_nodes = set()
        coastline_nodes = Pathing.is_coast()

        for node in coastline_nodes:
            if node.is_valid():
                coastal_nodes.add(node)
        
        return coastal_nodes
    
    def init_coastline(self, coastline_data):
        self.coastal_nodes = set(coastline_data)
    
    def is_coastal_node(self, node):
        return node in self.coastal_nodes
    
    end_time = time.time()
    comp_time = end_time - start_time
    print(f"Grid Map: {comp_time}")

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
    start_time = time.time()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    land = gpd.read_file("routing/data/geopackages/ne_10m_land.gpkg")
    coastline = gpd.read_file("routing/data/geopackages/ne_10m_coastline.gpkg")

    def __init__(self, grid_map):

        self.grid_map = grid_map

    @staticmethod
    def is_land():
        land_areas = []
        node_id = 0
        for _, row in Pathing.land.iterrows():
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
        for _, row in Pathing.coastline.iterrows():
            if isinstance(row["geometry"], LineString):
                coastline += [Node(node_id,y,x) for x, y in row["geometry"].coords]
                node_id +=len(row["geometry"].coords)

            elif isinstance(row["geometry"], MultiLineString):
                for line in row["geometry"].geoms:
                    coastline += [Node(node_id,y,x) for x, y in line.coords]
                    node_id +=len(line.coords)
        return coastline
    
    def connect_coastline_gaps(coastline_nodes, max_gap_distance):

        connected_coastline = []
        node_id = len(coastline_nodes)

        for i in range(len(coastline_nodes)-1):
            current_node = coastline_nodes[i]
            next_node = coastline_nodes[i+1]
            gap_distance = GridMap.calculate_distance(current_node, next_node)

            if gap_distance > max_gap_distance:
                new_lat = (current_node.lat + next_node.lat) / 2
                new_lon = (current_node.lon + next_node.lon) / 2
                new_node = Node(node_id, new_lat, new_lon)
                connected_coastline.extend([current_node, new_node])
                node_id += 1

            else:
                connected_coastline.append(current_node)

        connected_coastline.append(coastline_nodes[-1])

        return connected_coastline
    
    def is_near_coast(point, coast_lines, threshold):
        shapely_point = Point(point[1], point[0])

        if not shapely_point.is_valid:
            raise ValueError(f"Invalid point geometry: {shapely_point}")
        
        for line in coast_lines:
            shapely_line = LineString(line)
            if not shapely_line.is_valid:
                raise ValueError(f"Invalid line geometry: {shapely_line}")
            
            #rough conversion from degrees to kilometers
            if shapely_point.distance(shapely_line) / 111.32 > threshold :
                return True
        return False
    
    def near_coast_proximity(grid, coast_lines, threshold):
        for x in range(len(grid)):
            for y in range(len(grid[x])):
                if Pathing.is_near_coast((x, y), coast_lines, threshold):
                    grid[x][y].walkable = False
        print("Found near coast proximity")

    
    
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
    
    def heuristic(node1, node2):
        return great_circle((node1.lat, node1.on), (node2.lat, node2.lon)).km

    def a_star(self, start_node, end_node):
        visited = set()
        open_set = []
        heapq.heappush(open_set, (0, start_node))

        came_from = {}
        g_score = {node: float("infinity") for node in self.nodes.values()}
        g_score[start_node] = 0

        f_score = {node: float("infinity") for node in self.nodes.values()}
        f_score[start_node] = self.heuristic(start_node, end_node)

        while open_set:
            current = heapq.heappop(open_set[1])

            if current == end_node:
                return self.reconstruct_path(came_from, current)
            visited.add(current)

            for neighbor in current.neighbors:
                if neighbor in visited:
                    continue

                tentative_g_score = g_score[current] + current.distance[neighbor]

                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, end_node)

                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        #in case of no path      
        return None
    
    def reconstruct_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.insert(0, current)
        return total_path
        
    def dijkstra(self, start_node, end_node):

        land_data = grid_map.land_nodes()
        grid_map.init_land(land_data)
        coastline_data = Pathing.is_coast()
        max_gap_distance = 0.5
        connected_coastline = Pathing.connect_coastline_gaps(coastline_data, max_gap_distance)
        grid_map.init_coastline(coastline_data)

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

    end_time = time.time()
    comp_time = end_time - start_time
    print(f"Pathing: {comp_time}")
