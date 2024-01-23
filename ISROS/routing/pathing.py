import folium
from folium.plugins import AntPath
import networkx as nx
import osmnx as ox


class GridMap:
    def __init__(self, bounds, resolution):
        self.bounds = bounds # ((min_x, min_y), (max_x, max_y))
        self.resolution = resolution
        self.grid = self.create_grid()
        self.graph = self.create_graph()


class Pathing:
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