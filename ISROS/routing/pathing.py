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
        # Buffer in degrees to account for the granularity of the grid
        buffer = 0.005
        # Use a simple box around the point to represent the grid cell
        north, south, east, west = lat + buffer, lat - buffer, lon + buffer, lon - buffer
        # Create a polygon to represent the grid cell
        polygon = ox.utils_geo.bbox_to_poly(north, south, east, west)
        
        # Query OSM for water bodies within the polygon
        water = ox.geometries_from_polygon(polygon, tags={'natural': 'water', 'landuse': 'reservoir'})
        
        # If there are water bodies in the cell, it is not land
        return water.empty


        
    def grid_coordinate(self, location):
        #convert a real-world coordinate to a grid coordinate
        pass

    def real_coordinate(self, grid_location):
        #convert a grid coordinate back to a real-world coordinate
        pass
    
    def a_star(start, goal, grid):
        #perform a_star pathing
        pass