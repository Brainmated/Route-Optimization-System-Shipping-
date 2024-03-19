import pickle
import math
import os
import networkx as nx
from queue import PriorityQueue
from scipy.spatial import cKDTree

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'grid_map', 'sea_grid.pkl')

# Check if the file exists
if not os.path.isfile(file_path):
    print(f"Error: The file {file_path} does not exist. Check the file path.")
    print(f"Current working directory: {os.getcwd()}")

# Load the sea grid DataFrame from the .pkl file
with open(file_path, 'rb') as file:
    sea_grid = pickle.load(file)

# Filter the DataFrame to include only water cells
water_grid = sea_grid[sea_grid['is_water']]

# Create a graph
G = nx.Graph()

# Add nodes and edges to the graph
for index, row in water_grid.iterrows():
    node = (row['longitude'], row['latitude'])
    G.add_node(node)
    # Connect to adjacent nodes (assuming a regular grid with 0.1 degree steps)
    for delta_lon in [-0.1, 0.1]:
        neighbor_lon = node[0] + delta_lon
        if ((neighbor_lon, node[1]) in G.nodes):
            G.add_edge(node, (neighbor_lon, node[1]))
    for delta_lat in [-0.1, 0.1]:
        neighbor_lat = node[1] + delta_lat
        if ((node[0], neighbor_lat) in G.nodes):
            G.add_edge(node, (node[0], neighbor_lat))

# Haversine formula to calculate the distance between two points on the Earth's surface
def haversine(coord1, coord2):
    R = 6371  # Earth radius in kilometers
    lat1, lon1 = math.radians(coord1[1]), math.radians(coord1[0])
    lat2, lon2 = math.radians(coord2[1]), math.radians(coord2[0])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def get_closest_navigable_node(graph, point):
    # Round the point's coordinates to 6 decimal places before querying
    point = (round(point[0], 3), round(point[1], 3))
    
    # Extract the navigable nodes from the graph and round them to 6 decimal places
    navigable_nodes = [(round(node[0], 3), round(node[1], 3)) for node in graph.nodes]
    
    # Create a k-d tree for efficient nearest neighbor search
    tree = cKDTree(navigable_nodes)
    
    # Find the closest node in the sea grid to the given point
    distance, index = tree.query(point)
    closest_navigable_node = navigable_nodes[index]
    return closest_navigable_node

# A* algorithm
def a_star(graph, start, goal):

    start = get_closest_navigable_node(graph, start)
    goal = get_closest_navigable_node(graph, goal)

    frontier = PriorityQueue()
    frontier.put((0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    
    while not frontier.empty():
        current = frontier.get()[1]
        
        if current == goal:
            break
        
        for neighbor in graph.neighbors(current):
            new_cost = cost_so_far[current] + haversine(current, neighbor)
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + haversine(neighbor, goal)
                frontier.put((priority, neighbor))
                came_from[neighbor] = current
    
    # Reconstruct path
    current = goal
    path = []
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()
    return path

# Dijkstra's algorithm
def dijkstra(graph, start, goal):

    start = get_closest_navigable_node(graph, start)
    goal = get_closest_navigable_node(graph, goal)

    frontier = PriorityQueue()
    frontier.put((0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    
    while not frontier.empty():
        current = frontier.get()[1]
        
        if current == goal:
            break
        
        for neighbor in graph.neighbors(current):
            new_cost = cost_so_far[current] + haversine(current, neighbor)
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                frontier.put((new_cost, neighbor))
                came_from[neighbor] = current
    
    # Reconstruct path
    current = goal
    path = []
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()
    return path