import folium
from folium.plugins import AntPath
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
        self.land_data = gpd.read_file("E:/Programming in Python/applications/Thesis/ISROS/routing/data/ne_10m_land.shp")
        self.ocean_data = gpd.read_file("E:/Programming in Python/applications/Thesis/ISROS/routing/data/ne_10m_ocean.shp")

    
    def get_random_point(self, data):
        random_feature = data.sample(1)
        geom = random_feature.geometry.iloc[0]

        # Handle MultiPolygon geometries
        if geom.geom_type == 'MultiPolygon':
            # Choose a random Polygon from the MultiPolygon
            geom = random.choice([poly for poly in geom.geoms])
        
        # Assuming the geometry is Polygon, we'll return a random point from within
        return geom.representative_point().coords[0]

    #---------------------------------THE SHP FILES ARE VALID----------------------------------
    #---------------------------------CHECK WHY THE RANDOM POSITIONS ARENT THAT RANDOM---------
    def mark_points(self, m):
        # Get a random point from land and ocean data respectively
        land_point = self.get_random_point(self.land_data)
        ocean_point = self.get_random_point(self.ocean_data)
        #print(land_point)
        print(ocean_point)
        # Create a red marker for the random land point
        folium.Marker(
            [land_point[1], land_point[0]], 
            popup='Random Land Point',
            icon=folium.Icon(color='red')
        ).add_to(m)

        # Create a green marker for the random ocean point
        folium.Marker(
            [ocean_point[1], ocean_point[0]], 
            popup='Random Ocean Point',
            icon=folium.Icon(color='green')
        ).add_to(m)

    def print_column_headers(self):
        # Print the column names for the land data
        print("Land Data Columns:")
        print(self.land_data.columns)

        # Print the column names for the ocean data
        print("Ocean Data Columns:")
        print(self.ocean_data.columns)



class Pathing:

    land = gpd.read_file("E:/Programming in Python/applications/Thesis/ISROS/routing/data/ne_10m_land.shp")
    ocean = gpd.read_file("E:/Programming in Python/applications/Thesis/ISROS/routing/data/ne_10m_ocean.shp")
    coastline = gpd.read_file("E:/Programming in Python/applications/Thesis/ISROS/routing/data/ne_10m_coastline.shp")


    def __init__(self, location1, location2, grid_map):
        self.location1 = location1
        self.location2 = location2
        self.grid_map = grid_map

    def is_land(lat, lon):
        
        point = Point(lon, lat)
        return Pathing.land.contains(point).any()

    def is_sea(lat, lon):
        point = Point(lon, lat)
        return Pathing.ocean.contains(point).any()

    
    def a_star(start, goal, grid):
        #perform a_star pathing
        pass