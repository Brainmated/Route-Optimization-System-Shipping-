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
        #Get a random point from land and ocean data respectively
        land_point = self.get_random_point(self.land_data)
        coastline_point = self.get_random_point(self.coastline_data)
        #print(land_point)
        print(coastline_point)
        #Create a red marker for the random land point
        folium.Marker(
            [land_point[1], land_point[0]], 
            popup='Random Land Point',
            icon=folium.Icon(color='red')
        ).add_to(m)

        #Create a green marker for the random coastline point
        folium.Marker(
            [coastline_point[1], coastline_point[0]], 
            popup='Random Coastline Point',
            icon=folium.Icon(color='green')
        ).add_to(m)



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
        lines = []
        print("land test")
        for _, row in Pathing.land.iterrows():
            if isinstance(row['geometry'], (LineString, MultiLineString)):
                if isinstance(row['geometry'], LineString):
                    # Extract the coordinates of the LineString
                    coords = list(row['geometry'].coords)
                else:
                    # Flatten the MultiLineString into a list of coordinates
                    coords = [pt for line in row['geometry'] for pt in list(line.coords)]
                lines.append(coords)
        return lines
    
    def is_ocean():
        pass
    
    @staticmethod
    def is_coast():
        lines = []
        for _, row in Pathing.coastline.iterrows():
            if isinstance(row['geometry'], LineString):
                coords = list(row['geometry'].coords)
                # Ensure coords are in (longitude, latitude) order
                coords = [(x, y) for x, y in coords]
                lines.append(coords)
            elif isinstance(row['geometry'], MultiLineString):
                for line in row['geometry']:
                    coords = list(line.coords)
                    # Ensure coords are in (longitude, latitude) order
                    coords = [(x, y) for x, y in coords]
                    lines.append(coords)
        return lines

    
    def a_star(start, goal, grid):
        #perform a_star pathing
        pass

    def get_path_coordinates():
        pass