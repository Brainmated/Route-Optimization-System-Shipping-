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
from shapely.geometry import Point, Polygon


class Node:
    def __init__(self, lat, lon):
        self.lat = float(lat) if lat is not None else None
        self.lon = float(lon) if lon is not None else None
        self.neighbors = []

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return (self.lat, self.lon) == (other.lat, other.lon)
    
    def __hash__(self):
        return hash((self.lat, self.lon))
    
    def is_valid(self):
        return self.lat is not None and self.lon is not None and -90 <= self.lat <= 90 and -180 <= self.lon <= 180

'''
The GridMap class creates a node for every integer latitude/longitude
intersection and then adds edges to each node's neighbors.
With 8 possible directions of movement the add_edges() method
handles wrapping of the map so the eastern most and western most edges connect.
'''

class GridMap:
    
    #current method will test for the 1° x 1° grid
    def __init__(self, resolution=1.0):
        self.resolution = resolution
        self.nodes = self.create_nodes()
        self.coastal_nodes = self.coastal_nodes()
        self.add_edges()

    #method that creates nodes on the grid to help map the cells
    def create_nodes(self):
        #set nodes as a dictionary and set attributes
        nodes = {}
        for lat in np.arange(-90, 90, self.resolution):
            for lon in np.arange(-180, 180, self.resolution):
                nodes[(float(lat), float(lon))] = Node(lat, lon)
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
                    node.neighbors.append(neighbor)

    def get_node(self, lat, lon):
        
        grid_lat = float(round(lat/self.resolution) * self.resolution)
        grid_lon = float(round(lon/self.resolution) * self.resolution)

        #wrap longitude if necessary
        if grid_lon <= -180:
            grid_lon += 360
        elif grid_lon > 180:
            grid_lon -= 360
        return self.nodes.get((grid_lat, grid_lon))
    
    def coastal_nodes(self):
        coastal_nodes = set()
        coastline_segments = Pathing.is_coast()

        for segment in coastline_segments:
            for node in segment:
                if node.is_valid():
                    coastal_nodes.add(node)
        
        return coastal_nodes
    
    def is_coastal_node(self, node):
        return node in self.coastal_nodes
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

    script_dir = os.path.dirname(os.path.abspath(__file__))
    land = gpd.read_file("routing/data/ne_10m_land.shp")
    coastline = gpd.read_file("routing/data/ne_10m_coastline.shp")


    
    def __init__(self, grid_map):

        self.grid_map = grid_map

    @staticmethod
    def is_land():
        pass
    
    def is_ocean():
        pass
    
    #------------------------SUCCESS-------------------------------------------------------------
    @staticmethod
    def is_coast():
        coastline = []
        for _, row in Pathing.coastline.iterrows():
            if isinstance(row["geometry"], LineString):
                coastline += [Node(y,x) for x, y in row["geometry"].coords]
            elif isinstance(row["geometry"], MultiLineString):
                for line in row["geometry"]:
                    coastline += [Node(y,x) for x, y in line.coords]
        return coastline
    
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
        

    def a_star(request, grid_map):
        try:
            loc_a_name = request.POST.get("locationA")
            loc_b_name = request.POST.get("locationB")
            ports = parse_ports()

            start_coords = next((port for port in ports if port["name"] == loc_a_name), None)
            print(f"start_coords = {start_coords}")
            goal_coords = next((port for port in ports if port["name"] == loc_b_name), None)
            print(f"goald_coords = {goal_coords}")
            
            start = grid_map.get_node(float(start_coords["latitude"]), float(start_coords["longitude"]))
            print(f"Initial node set, {start}")
            goal = grid_map.get_node(float(goal_coords["latitude"]), float(goal_coords["longitude"]))
            print(f"End node set, {goal}")

            if start is None or goal is None:
                messages.error(request, "One or both locations not found.")
                return None
            
            if not start.is_valid or not goal.is_valid:
                raise ValueError("One or more nodes are invalid.")
            
            
            #DEBUG------------------------------------------------------------------
            print(f"Debugging: Start Node: {start}, Goal Node: {goal}")
            
            #implement Heuristics
            def haversine(lat1, lon1, lat2, lon2):
                #convert decimal degrees to radians
                lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

                #Haversine formula
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                #earth radius in kilometers
                km = 6371 * c
                return km
            
            #open and closed sets 
            #open sets contain nodes that have been discovered but not evaluated
            open_set = []
            open_set_tracker = set()
            heapq.heappush(open_set, (0, start))
            open_set_tracker.add(start)
            #DEBUG--------------------------------------------------------------------
            print(f"Open set tracker before removing the current node: {open_set_tracker}")
            #closed sets contain nodes that have been evaluated
            closed_set = set()

            #distance and movement cost from initial/start state to current node
            g_score = {node: float("inf") for node in grid_map.nodes.values()}
            g_score[start] = 0 #the initial state, position 0

            #estimated movement cost from current node to end/goal node
            f_score = {node: float("inf") for node in grid_map.nodes.values()}
            f_score[start] = haversine(start.lat, start.lon, goal.lat, goal.lon)
            #DEBUG-------------------------------------------------------------------------------
            print(f"Debugging: Initial heuristic value: {f_score[start]}")
            #path reconstruction
            came_from = {}

            coast_lines = Pathing.is_coast()

            #threshold of at least 10 km away from the coast
            threshold = 10

            def reconstruct_path(came_from, current):
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(current)
                path.reverse()
                return path
    
            while open_set:

                #search for node in open set with the lowest f_score value
                current = heapq.heappop(open_set)[1]
                open_set_tracker.remove(current)
                #DEBUG-----------------------------------------------------------------
                print(f"Debugging: Current Node: {current}") 

                if current == goal:
                    print("Debugg: Goal reached, reconstructing path.")
                    return reconstruct_path(came_from, current)
                
                closed_set.add(current)

                for neighbor in current.neighbors:
                    #DEBUG-----------------------------------------------------------------
                    print(f"Debugging: Evaluating neighbor: {neighbor}")
                    if Pathing.is_near_coast((neighbor.lat, neighbor.lon), coast_lines, threshold):
                        #DEBUG----------------------------------------------------------------------
                        print(f"Debugging: Neighbor {neighbor} is near coast and will be skipped.")
                        continue
                    
                    if neighbor in closed_set:
                        #ignore evaluated neighbors and continue
                        continue

                    #hesitant approach
                    tentative_g_score = g_score[current] + haversine(current.lat, current.lon, neighbor.lat, neighbor.lon)
                    #DEBUG-----------------------------------------------------------------------------
                    print(f"Debugging: Tentative G Score for {neighbor}: {tentative_g_score}")

                    if tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + haversine(neighbor.lat, neighbor.lon, goal.lat, goal.lon)

                        # Add the neighbor to the open set if it's not there already
                        if neighbor not in open_set_tracker:
                            heapq.heappush(open_set, (f_score[neighbor], neighbor))
                            open_set_tracker.add(neighbor)
                    
                    #when a node is popped from the open set, then remove it from the tracker
                    open_set_tracker.remove(current)
                    
                    #BEST PATH
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score +haversine(neighbor.lat, neighbor.lon, goal.lat, goal.lon)

            #the optimal path isnt found
            return None
        except KeyError as e:
            print(f"Key error encountered: {e}")
            print(f"Current state of open_set_tracker: {open_set_tracker}")
    
    def dijkstra(self, request, grid_map):

        coastline_data = Pathing.is_coast()
        grid_map = GridMap(coastline_data)

        loc_a_name = request.POST.get("locationA")
        loc_b_name = request.POST.get("locationB")
        
        ports = parse_ports() 
        
        loc_a = next((port for port in ports if port["name"] == loc_a_name), None)
        loc_b = next((port for port in ports if port["name"] == loc_b_name), None)
        
        if loc_a is None or loc_b is None:
            raise ValueError("One or both locations not found.")
        
        loc_a_coord = (float(loc_a['latitude']), float(loc_a['longitude']))
        loc_b_coord = (float(loc_b['latitude']), float(loc_b['longitude']))
        
        # Convert coordinates to nodes
        start_node = grid_map.get_node(*loc_a_coord)
        end_node = grid_map.get_node(*loc_b_coord)
        
        # Initialize distances and previous nodes
        distances = {node: float('infinity') for node in grid_map.nodes.values()}
        previous_nodes = {node: None for node in grid_map.nodes.values()}
        distances[start_node] = 0
        
        # Initialize priority queue and add the start node
        pq = [(0, start_node)]
        
        while pq:
            current_distance, current_node = heapq.heappop(pq)
            
            if current_node == end_node:
                break  # We found the shortest path to the end node
            
            for neighbor in current_node.neighbors:
                # Check if the neighbor is a coastline or near a coastline
                if self.is_coastal_node(neighbor):
                    continue  # Skip the neighbor if it's not passable
                
                # Calculate the distance to the neighbor
                distance = great_circle((current_node.lat, current_node.lon), (neighbor.lat, neighbor.lon)).kilometers
                new_distance = current_distance + distance
                
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(pq, (new_distance, neighbor))
        
        # Reconstruct the path from end_node to start_node
        path = []
        current = end_node
        while current is not None:
            path.insert(0, current)
            current = previous_nodes[current]
        
        # Convert nodes back to coordinates for the output path
        path_coordinates = [(node.lat, node.lon) for node in path]
        
        return path_coordinates
        

    def visibility_graph():
        pass
