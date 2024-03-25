import os
import pickle
import networkx as nx
import pandas as pd
import numpy as np
import gc
import math

from sklearn.neighbors import BallTree

def debug_print(message):
    print(f"DEBUG: {message}")

script_dir = os.path.dirname(os.path.abspath(__file__))
debug_print(f"Script directory: {script_dir}")

file_path = os.path.join(script_dir, 'grid_map', 'sea_grid.pkl')
graph_file_path = os.path.join(script_dir, 'grid_map', 'sea_graph.pkl')
debug_print(f"Grid file path: {file_path}")
path_print = os.path.join(script_dir, 'data')

def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of Earth in kilometers. Use 3956 for miles
    r = 6371

    # Calculate the result
    return c * r

def add_edges_knn(G, nodes, k, batch_size=1000):
    # Convert latitude and longitude to radians for BallTree
    nodes_rad = np.radians(nodes)
    tree = BallTree(nodes_rad, metric='haversine')

    # Perform batch query of the BallTree for k nearest neighbors
    for i in range(0, len(nodes), batch_size):
        # Find the indices of k nearest neighbors for the batch
        distances, indices = tree.query(nodes_rad[i:i + batch_size], k + 1)

        # Iterate through each node and its neighbors
        for j, neighbors in enumerate(indices):
            node_idx = i + j  # Actual index of the node
            node = nodes[node_idx]
            for neighbor_idx in neighbors[1:]:  # Skip the first index (node itself)
                neighbor = nodes[neighbor_idx]
                # Add an edge to the graph
                G.add_edge(node, neighbor)

def generate_or_load_graph(file_path, graph_file):

    if os.path.isfile(graph_file):
        print(f"Graph file found at {graph_file}. Loading graph...")
        with open(graph_file, 'rb') as file:
            G = pickle.load(file)
        print("Graph successfully loaded.")
    else:
        print("Graph file not found. Generating new graph...")
        G = nx.Graph()
        print("Loading sea grid and adding nodes and edges to the graph...")

        sea_grid = pd.read_pickle(file_path)
        water_grid = sea_grid[sea_grid['is_water'] == 1]
        step_size = 1

        # Add all nodes in a batch
        nodes = [(row['latitude'], row['longitude']) for index, row in water_grid.iterrows()]
        G.add_nodes_from(nodes)
        seen_nodes = set(nodes)

        # Add all edges in a batch
        add_edges_knn(G, nodes, k=step_size, batch_size=1000)

        print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

        with open(graph_file, 'wb') as file:
            pickle.dump(G, file)
        print(f"Graph saved to {graph_file}")

    return G 

    
def write_isolated_nodes_to_file(graph, output_file="isolated_nodes.txt", checkpoint_file="checkpoint.txt", write_to_file=True):
    if graph is None:
        raise ValueError("No graph object provided. Ensure the graph is loaded correctly.")
    
    isolated_nodes = list(nx.isolates(graph))
    debug_print(f"There are {len(isolated_nodes)} isolated nodes in the graph.")
    
    last_processed_index = 0
    # Load the last processed index from the checkpoint file if it exists
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            last_processed_index = int(f.read().strip())
        debug_print(f"Resuming from index: {last_processed_index}")  # Debug print for resuming index
    
    batch_size = 1000  # Process nodes in batches
    node_infos = []  # Buffer for isolated node information

    # Determine the latitude and longitude bounds
    lats = [node[0] for node in graph.nodes]
    lons = [node[1] for node in graph.nodes]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)

    # Divide the area into blocks (e.g., 4x5 grid)
    lat_blocks = np.linspace(lat_min, lat_max, 5) # Adjust the number of blocks as needed
    lon_blocks = np.linspace(lon_min, lon_max, 5) # Adjust the number of blocks as needed

    # Create a dictionary to hold counts of isolated nodes for each block
    block_counts = {(i, j): 0 for i in range(len(lat_blocks)-1) for j in range(len(lon_blocks)-1)}

    if write_to_file:
        with open(output_file, 'a') as file:
            for i in range(last_processed_index, len(isolated_nodes)):
                node = isolated_nodes[i]
                node_infos.append(f"{node[0]},{node[1]}\n")

                # Assign isolated nodes to blocks
                lat, lon = node
                for i in range(len(lat_blocks)-1):
                    for j in range(len(lon_blocks)-1):
                        if lat_blocks[i] <= lat < lat_blocks[i+1] and lon_blocks[j] <= lon < lon_blocks[j+1]:
                            block_counts[(i, j)] += 1

                # Write in batches and update the checkpoint file
                if len(node_infos) >= batch_size or i == len(isolated_nodes) - 1:
                    file.writelines(node_infos)  # Write buffered node information
                    node_infos = []  # Clear the buffer
                    
                    # Update the checkpoint
                    with open(checkpoint_file, 'w') as f:
                        f.write(str(i))
                    
    # Debug print to show the block counts
    for block, count in block_counts.items():
        debug_print(f"Block {block} contains {count} isolated nodes.")
    
    return block_counts

def find_and_print_closest_neighbors(nodes, start_coord, k=10):
    # Convert latitude and longitude to radians for BallTree
    nodes_rad = np.radians(nodes)
    start_coord_rad = np.radians([start_coord])
    
    # Create a BallTree with the nodes
    tree = BallTree(nodes_rad, metric='haversine')

    # Query the tree for the k nearest neighbors to start_coord
    distances, indices = tree.query(start_coord_rad, k+1)  # k+1 because the point itself may be included

    # Print the k nearest neighbors, skipping the first if it is the start_coord itself
    for i, index in enumerate(indices[0]):
        # Skip if the first point is the same as the start_coord
        if distances[0][i] == 0:
            continue
        neighbor = nodes[index]
        distance_km = distances[0][i] * 6371  # Convert from radians to kilometers
        direction = get_cardinal_direction(start_coord[0], start_coord[1], neighbor[0], neighbor[1])
        print(f"Neighbor {i}: {neighbor}, Distance: {distance_km:.2f} km, Direction: {direction}")

def get_cardinal_direction(start_lat, start_lon, end_lat, end_lon):
    lat_diff = end_lat - start_lat
    lon_diff = end_lon - start_lon

    if lat_diff > 0 and lon_diff > 0:
        return 'NE'
    elif lat_diff < 0 and lon_diff > 0:
        return 'SE'
    elif lat_diff < 0 and lon_diff < 0:
        return 'SW'
    elif lat_diff > 0 and lon_diff < 0:
        return 'NW'
    elif lat_diff == 0 and lon_diff > 0:
        return 'E'
    elif lat_diff == 0 and lon_diff < 0:
        return 'W'
    elif lat_diff > 0 and lon_diff == 0:
        return 'N'
    elif lat_diff < 0 and lon_diff == 0:
        return 'S'
    else:
        return 'Origin'

def interpolate_coordinates(start_coord, goal_coord, num_points=100):
    x_coords = [start_coord[0] + i * (goal_coord[0] - start_coord[0]) / (num_points - 1) for i in range(num_points)]
    y_coords = [start_coord[1] + i * (goal_coord[1] - start_coord[1]) / (num_points - 1) for i in range(num_points)]
    return list(zip(x_coords, y_coords))

# The script's execution part, if needed:
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'grid_map', 'sea_grid.pkl')
    graph_file_path = os.path.join(script_dir, 'grid_map', 'sea_graph.pkl')

    start_coord = (40.68, -74.01)
    goal_coord = (-10.26, 40.13)
    #G = generate_or_load_graph(file_path, graph_file_path)
    #nodes = list(G.nodes)
    #find_and_print_closest_neighbors(nodes, start_coord, k=20)
    #find_and_print_closest_neighbors(nodes, goal_coord, k=20)
    #write_isolated_nodes_to_file(G)

    # Interpolate the coordinates
    interpolated_coords = interpolate_coordinates(start_coord, goal_coord)

    # Write the coordinates to a file
    coord_paths_file_path = os.path.join(script_dir, 'coord_paths.txt')
    with open(coord_paths_file_path, 'w') as file:
        for coord in interpolated_coords:
            file.write(f"{coord}\n")
    
    print(f"Interpolated coordinates have been written to {coord_paths_file_path}")

__all__ = ['generate_or_load_graph', 'write_isolated_nodes_to_file', 'file_path', 'graph_file_path']
