import folium
from folium.plugins import AntPath
import networkx as nx


class GridMap:
    def __init__(self, bounds, resolution):
        self.bounds = bounds # ((min_x, min_y), (max_x, max_y))
        self.resolution = resolution
        self.grid = self.create_grid()
        self.graph = self.create_graph()

    def create_grid(self):
        # This function would discretize the map area into a grid based on the bounds and resolution
        # Not implemented here, but would return a 2D array or similar structure representing the grid
        pass
    
    def create_graph(self):
        # This function would convert the grid into a graph where each cell is a node and adjacent cells are linked by edges
        # Not implemented here, but would return a graph structure, possibly using NetworkX or a similar library
        pass


class Pathing:
    def __init__(self, location1, location2, grid_map):
        self.location1 = location1
        self.location2 = location2
        self.grid_map = grid_map

    def find_path(self):
        try:
            # Convert real-world coordinates to grid coordinates
            start_node = self.grid_coordinate(self.location1)
            end_node = self.grid_coordinate(self.location2)

            # Use a pathfinding algorithm like A* to calculate the shortest path on the grid.
            path = nx.astar_path(self.grid_map.graph, start_node, end_node)
            # Convert the path back to real-world coordinates
            real_path = [self.real_coordinate(node) for node in path]

            return real_path
        except Exception as e:
            print(f"An error occurred in find_path: {e}")
            # Handle the error or return a default value
            return []
        

    def grid_coordinate(self, location):
        # Convert a real-world coordinate to a grid coordinate
        pass

    def real_coordinate(self, grid_location):
        # Convert a grid coordinate back to a real-world coordinate
        pass

    def get_map(self):
        try:
            path = self.find_path()
            if not path:
                raise ValueError("Unable to find path.")

            # Create a folium map object, centered on the start of the path
            m = folium.Map(location=self.location1, zoom_start=12)

            # Add the grid to the map (assuming self.grid_map.resolution is the desired spacing)
            self.add_grid_to_map(m, self.grid_map.resolution)

            # Add markers for the start and end points
            folium.Marker(self.location1, tooltip='Start').add_to(m)
            folium.Marker(self.location2, tooltip='End').add_to(m)
            
            # Draw a path between the two points if path exists
            if path:
                AntPath(locations=path).add_to(m)

            # Calculate the bounds of the path
            bounds = self.calculate_bounds(path)

            return m
        
        except Exception as e:
            print(f"An error occurred in get_map: {e}")
            # Return a default map
            return folium.Map(location=self.location1, zoom_start=12)
    
    def add_grid_to_map(self, map_obj, grid_spacing):
        min_x, min_y = self.bounds[0]
        max_x, max_y = self.bounds[1]
        
        # Calculate the number of grid lines needed
        num_lines_x = int((max_x - min_x) / grid_spacing) + 1
        num_lines_y = int((max_y - min_y) / grid_spacing) + 1

        # Draw the vertical grid lines
        for i in range(num_lines_x):
            x = min_x + i * grid_spacing
            folium.PolyLine(
                locations=[(min_y, x), (max_y, x)],
                color='blue',
                weight=1
            ).add_to(map_obj)

        # Draw the horizontal grid lines
        for j in range(num_lines_y):
            y = min_y + j * grid_spacing
            folium.PolyLine(
                locations=[(y, min_x), (y, max_x)],
                color='blue',
                weight=1
            ).add_to(map_obj)
            
    def calculate_bounds(self, path):
        # Assume path is a list of [lat, lng] points
        latitudes = [point[0] for point in path]
        longitudes = [point[1] for point in path]
        min_lat, max_lat = min(latitudes), max(latitudes)
        min_lng, max_lng = min(longitudes), max(longitudes)
        # Return the bounds in the format [(south_west), (north_east)]
        return [(min_lat, min_lng), (max_lat, max_lng)]