import folium
from folium.plugins import AntPath
import shapely.geometry
from shapely.geometry import Point, LineString, MultiLineString
import os
import numpy as np
import networkx as nx
import random
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
handles wrapping of the map so the eastern most and western most edges connect.'''
class GridMap:
    
    #current method will test for the 1° x 1° grid
    def __init__(self, resolution=1.0):
        self.resolution = resolution
        self.nodes = self.create_nodes()

    #method that creates nodes on the grid to help map the cells
    def create_nodes(self):

        #set nodes as a dictionary and set attributes
        nodes = {}
        for lat in np.arrange(-90, 90, self.resolution):
            for lon in np.arrange(-180, 180, self.resolution):
                nodes[(lat, lon)] = Node(lat, lon)
        return nodes
    

    def add_edges(self):

        #8 directions for the 8 edges of every node to move on
        directions = [
            (-1, 1), (-1, 0), (-1, 1) #Southwest | South |Southeast
            (0,1),            (0, 1)  #West | Node | East
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
    
    @staticmethod
    def is_near_coast(point, coast_lines, threshold):
        shapely_point = Point(point)
        for line in coast_lines:
            shapely_line = LineString(line)
            if shapely_point.distance(shapely_line) <= threshold:  # Corrected line
                return True
        return False
    
    def near_coast_proximity(grid, coast_lines, threshold):
        for x in range(len(grid)):
            for y in range(len(grid[x])):
                if Pathing.is_near_coast((x, y), coast_lines, threshold):
                    grid[x][y].walkable = True

    
    
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

        # Check if both locations were found
        if loc_a is None or loc_b is None:
            messages.error(request, "One or both locations not found.")
            # You may need to handle this case more gracefully, depending on how your application is structured
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

    def a_star(start, goal, grid, coast_lines):
        
        while not open_set.empty():
            current = open_set.get()[2]

            for neighbor in get_neighbors(current, grid):
                #check if the neighbor is near a coast
                if grid[neighbor.x][neighbor.y].walkable or is_near_coast((neighbor.x, neighbor.y), coast_lines, threshold):
                    pass
        pass

    def get_path_coordinates():
        pass

    def get_restrictions():
        #https://github.com/genthalili/searoute-py/issues/25
        pass