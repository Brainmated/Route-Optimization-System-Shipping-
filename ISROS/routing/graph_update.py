import os
import pickle
import networkx as nx
import pandas as pd
import numpy as np
import gc
import random
from scipy.spatial import cKDTree
import math
from math import radians
from itertools import islice

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

def add_weighted_edges(G):
    for edge in G.edges():
        lat1, lon1 = edge[0]
        lat2, lon2 = edge[1]
        distance = haversine(lat1, lon1, lat2, lon2)
        G[edge[0]][edge[1]]['weight'] = distance

def add_edges_knn(G, nodes, k, batch_size=1000, progress_callback=None):
    nodes_rad = np.radians(nodes)
    tree = BallTree(nodes_rad, metric='haversine')

    num_nodes = len(nodes)

    for i in range(0, num_nodes, batch_size):
        if progress_callback is not None:
            progress_callback(i, num_nodes)  # Call the progress callback function

        distances, indices = tree.query(nodes_rad[i:i + batch_size], k + 1)

        for j, neighbors in enumerate(indices):
            node_idx = i + j
            node = nodes[node_idx]
            for neighbor_idx in neighbors[1:]:
                neighbor = nodes[neighbor_idx]
                G.add_edge(node, neighbor)

def generate_or_load_graph(file_path, graph_file, k_neighbors=8):

    def report_progress(current_index, total_nodes):
        progress = (current_index / total_nodes) * 100
        print(f"Processing nodes: {progress:.2f}% complete.")

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

        nodes = [(row['latitude'], row['longitude']) for index, row in water_grid.iterrows()]
        G.add_nodes_from(nodes)

        add_edges_knn(G, nodes, k=k_neighbors, batch_size=500, progress_callback=report_progress)

        print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

        # New code starts here: Add custom nodes and connect them
    suez_canal = [
        (31.29, 32.34),
        (31.25, 32.30),
        (31.10, 32.30),
        (30.81, 32.31),
        (30.72, 32.32),
        (30.65, 32.34),
        (30.57, 32.33),
        (30.41, 32.36),
        (24.64, 35.99),
        (18.72, 39.15),
        (11.48, 44.78),
        (14.64, 52.29)
    ]

    # Add the new nodes to the graph
    G.add_nodes_from(suez_canal)

    # Connect the new nodes in a path
    for i in range(len(suez_canal) - 1):
        G.add_edge(suez_canal[i], suez_canal[i + 1])

    # Optionally, connect each new node to its nearest neighbor in the existing graph
    nodes = list(G.nodes)
    nodes_rad = np.radians(nodes)
    tree = BallTree(nodes_rad, metric='haversine')

    #apply random nodes with their buffer zone (50 neighbors) as non walkable
    weather_nodes = random.sample(list(G.nodes), 50)
    for node in weather_nodes:
        node_rad = np.radians([node])
        dist, ind = tree.query(node_rad, k=21)
        nearest_nodes = [nodes[i] for i in ind[0] if nodes[i] != node]

        #mark the 50 nearest neighbors as non walkable
        for neighbor_node in nearest_nodes:
            G.nodes[neighbor_node]['walkable'] = False

    for node in suez_canal:
        node_rad = np.radians([node])
        dist, ind = tree.query(node_rad, k=2)  # Query for the 2 nearest neighbors
        nearest_node = nodes[ind[0][1]]  # The first is the node itself, the second is the nearest neighbor
        G.add_edge(node, nearest_node)
    #add the weighted edges
    add_weighted_edges(G)

    # Save the updated graph to the .pkl file
    with open(graph_file, 'wb') as file:
        pickle.dump(G, file)
    print(f"Updated graph saved to {graph_file} with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

    return G, weather_nodes

def check_graph_connectivity(G):

    if nx.is_connected(G):
        print("The graph is connected.")
        return True
    else:
        print("The graph is not connected.")
        return False
    
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

def interpolate_points(start, end, num_points):
    """Generate interpolated points between start and end coordinates."""
    latitudes = np.linspace(start[0], end[0], num_points)
    longitudes = np.linspace(start[1], end[1], num_points)
    return zip(latitudes, longitudes)


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'grid_map', 'sea_grid.pkl')
    graph_file_path = os.path.join(script_dir, 'grid_map', 'sea_graph.pkl')

    # Generate the graph with nodes and edges, or load from file if already generated
    G = generate_or_load_graph(file_path, graph_file_path)

    # Check if the graph is connected
    connected = check_graph_connectivity(G)
