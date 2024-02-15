import folium
from folium.plugins import AntPath
from shapely.geometry import Point, LineString, MultiLineString
import os
import networkx as nx
import random
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point, Polygon


class GridMap:
    def __init__(self, bounds, resolution):
        self.bounds = bounds # ((min_x, min_y), (max_x, max_y))
        self.resolution = resolution
        self.grid = self.create_grid()
        self.graph = self.create_graph()

class Map_Marking:

    def __init__(self, land_shp, water_shp):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.land_data = gpd.read_file("routing/data/ne_10m_land.shp")
        self.coastline_data = gpd.read_file("routing/data/ne_10m_coastline.shp")


    #---------------------------------THE SHP FILES ARE VALID----------------------------------
    #---------------------------------CHECK WHY THE RANDOM POSITIONS ARENT THAT RANDOM---------

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
    def straight_path(m, location1, location2):
        folium.PolyLine([location1, location2], color="blue", weight=2.5, opacity=1).add_to(m)
        m.fit_bounds([location1, location2])

    def a_star(start, goal, grid):
        #perform a_star pathing
        pass

    def get_path_coordinates():
        pass

    def get_restrictions():
        #https://github.com/genthalili/searoute-py/issues/25
        pass