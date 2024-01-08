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
        # Convert real-world coordinates to grid coordinates
        start_node = self.grid_coordinate(self.location1)
        end_node = self.grid_coordinate(self.location2)

        # Use a pathfinding algorithm like A* to calculate the shortest path on the grid.
        path = nx.astar_path(self.grid_map.graph, start_node, end_node)
        # Convert the path back to real-world coordinates
        real_path = [self.real_coordinate(node) for node in path]

        return real_path

    def grid_coordinate(self, location):
        # Convert a real-world coordinate to a grid coordinate
        pass

    def real_coordinate(self, grid_location):
        # Convert a grid coordinate back to a real-world coordinate
        pass

    def get_map(self):
        path = self.find_path()
        # Create a folium map object, centered on the start of the path
        m = folium.Map(location=self.location1, zoom_start=12)

        # Add markers for the start and end points
        folium.Marker(self.location1, tooltip='Start').add_to(m)
        folium.Marker(self.location2, tooltip='End').add_to(m)
        
        # Draw a path between the two points
        AntPath(locations=path).add_to(m)

        # Calculate the bounds of the path
        bounds = self.calculate_bounds(path)

        # Restrict the map view to the path area with maxBounds
        m.fit_bounds(bounds)
        m.options['minZoom'] = 12  # Set the minimum zoom level (adjust as necessary)
        m.options['maxZoom'] = 17  # Set the maximum zoom level (adjust as necessary)

        # Apply the bounds to the map
        m.options['maxBounds'] = bounds
        # Set the bounds to be more rigid using maxBoundsViscosity
        m.options['maxBoundsViscosity'] = 1.0

        return m
    
    def calculate_bounds(self, path):
        # Assume path is a list of [lat, lng] points
        latitudes = [point[0] for point in path]
        longitudes = [point[1] for point in path]
        min_lat, max_lat = min(latitudes), max(latitudes)
        min_lng, max_lng = min(longitudes), max(longitudes)
        # Return the bounds in the format [(south_west), (north_east)]
        return [(min_lat, min_lng), (max_lat, max_lng)]