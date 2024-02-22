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
import osmnx as ox
import geopandas as gpd
from .ports import parse_ports
from django.contrib import messages
from geopy.distance import great_circle
from shapely.geometry import Point, Polygon


class Node:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.neighbors = []

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

    #method that creates nodes on the grid to help map the cells
    def create_nodes(self):

        #set nodes as a dictionary and set attributes
        nodes = {}
        for lat in np.arange(-90, 90, self.resolution):
            for lon in np.arange(-180, 180, self.resolution):
                nodes[(lat, lon)] = Node(lat, lon)
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

        return self.nodes.get((lat, lon))
        pass
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


    
    def __init__(self, location1, location2, grid_map):
        self.location1 = location1
        self.location2 = location2
        self.grid_map = grid_map

    @staticmethod
    def is_land():
        pass
    
    def is_ocean():
        pass
    
    #------------------------SUCCESS-------------------------------------------------------------
    @staticmethod
    def is_coast():
        lines = []
        # Iterate through each row of the coastline GeoDataFrame
        for _, row in Pathing.coastline.iterrows():
            # Check if the geometry is a LineString
            if isinstance(row['geometry'], LineString):
                # Swap the coordinates from (lon, lat) to (lat, lon)
                coords = [(y, x) for x, y in row['geometry'].coords]
                lines.append(coords)
            # Check if the geometry is a MultiLineString
            elif isinstance(row['geometry'], MultiLineString):
                # Extract coordinates from each component LineString
                for line in row['geometry']:
                    # Swap the coordinates from (lon, lat) to (lat, lon)
                    coords = [(y, x) for x, y in line.coords]
                    lines.append(coords)
        return lines
    
    def is_near_coast(self, point, coast_lines, threshold):
        shapely_point = Point(point[1], point[0])

        for line in coast_lines:
            shapely_line = LineString(line)

            #rough conversion from degrees to kilometers
            if shapely_point.distance(shapely_line) / 111.32 > threshold :
                return True
        
        return False
    
    def near_coast_proximity(grid, coast_lines, threshold):
        for x in range(len(grid)):
            for y in range(len(grid[x])):
                if Pathing.is_near_coast((x, y), coast_lines, threshold):
                    grid[x][y].walkable = False

    
    
    @staticmethod
    def straight_path(request, map_obj):
        # Extract location A and B from the POST data
        loc_a_name = request.POST.get("locationA")
        loc_b_name = request.POST.get("locationB")

        # Assume parse_ports() function returns a list of ports with their details (implement this)
        ports = parse_ports()  # This function needs to be defined elsewhere in your application

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

    def a_star(request, grid_map):

        loc_a_name = request.POST.get("locationA")
        loc_b_name = request.POST.get("locationB")
        ports = parse_ports()

        start_coords = next((port for port in ports if port["name"] == loc_a_name), None)
        goal_coords = next((port for port in ports if port["name"] == loc_b_name), None)
        
        start = grid_map.get_node(start_coords["latitude"], start_coords["longitude"])
        goal = grid_map.get_node(goal_coords["latitude"], goal_coords["longitude"])

        if start is None or goal is None:
            messages.error(request, "One or both locations not found.")
            return None
        
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

        #closed sets contain nodes that have been evaluated
        closed_set = set()

        #distance and movement cost from initial/start state to current node
        g_score = {node: float("inf") for node in grid_map.nodes.values()}
        g_score[start] = 0 #the initial state, position 0

        #estimated movement cost from current node to end/goal node
        f_score = {node: float("inf") for node in grid_map.nodes.values()}
        f_score[start] = haversine(start.lat, start.lon, goal.lat, goal.lon)

        #path reconstruction
        came_from = {}

        coast_lines = Pathing.is_coast()

        #threshold of at least 10 km away from the coast
        threshold = 10

        while open_set:

            #search for node in open set with the lowest f_score value
            current = heapq.heappop(open_set)[1]

            if current == goal:

                #reconstruct the path
                path = []

                while current in came_from:
                    #add to the path
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                
                #return the reversed path
                return path[::-1]  
            
            closed_set.add(current)

            for neighbor in current.neighbors:

                if Pathing.is_near_coast((neighbor.lat, neighbor.lon), coast_lines, threshold):
                    continue
                
                if neighbor in closed_set:
                    #ignore evaluated neighbors and continue
                    continue

                #hesitant approach
                tentative_g_score = g_score[current] + haversine(current.lat, current.lon, neighbor.lat, neighbor.lon)

                #performance here is questionable
                if neighbor not in open_set_tracker:
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
                    open_set_tracker.add(neighbor)

                elif tentative_g_score >= g_score[neighbor]:
                    #not the best path
                    continue
                
                #when a node is popped from the open set, then remove it from the tracker
                open_set_tracker.remove(current)
                
                #BEST PATH
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score +haversine(neighbor.lat, neighbor.lon, goal.lat, goal.lon)
                

        #the optimal path isnt found
        return None
    
    def dijkstra():
        pass

    def visibility_graph():
        pass
