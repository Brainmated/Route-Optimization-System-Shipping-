import folium
from folium.plugins import AntPath
import networkx as nx


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
        #in the making
        pass
        
    def grid_coordinate(self, location):
        #convert a real-world coordinate to a grid coordinate
        pass

    def real_coordinate(self, grid_location):
        #convert a grid coordinate back to a real-world coordinate
        pass
    
    def a_star(start, goal, grid):
        #perform a_star pathing
        pass