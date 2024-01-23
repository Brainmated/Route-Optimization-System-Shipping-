import folium
from folium.plugins import AntPath
import os
import networkx as nx
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point, Polygon


class GridMap:
    def __init__(self, bounds, resolution):
        self.bounds = bounds # ((min_x, min_y), (max_x, max_y))
        self.resolution = resolution
        self.grid = self.create_grid()
        self.graph = self.create_graph()


class Pathing:

    land = gpd.read_file("E:/Programming in Python/applications/Thesis/ISROS/routing/data/ne_10m_land.shp")
    ocean = gpd.read_file("E:/Programming in Python/applications/Thesis/ISROS/routing/data/ne_10m_ocean.shp")
    coastline = gpd.read_file("E:/Programming in Python/applications/Thesis/ISROS/routing/data/ne_10m_coastline.shp")

    def __init__(self, location1, location2, grid_map):
        self.location1 = location1
        self.location2 = location2
        self.grid_map = grid_map

    def is_land(lat, lon):
        pass

    def is_sea(lat, lon):
        pass

    
    def a_star(start, goal, grid):
        #perform a_star pathing
        pass