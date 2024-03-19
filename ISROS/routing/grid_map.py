import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import pickle
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GridMap:
    def __init__(self, land_data_path, lat_min, lat_max, lon_min, lon_max, lat_step, lon_step):
        logging.debug("Initializing GridMap with land data from: {}".format(land_data_path))
        self.land = gpd.read_file(land_data_path)
        self.land_sindex = self.land.sindex
        self.grid_df = self.create_grid(lat_min, lat_max, lon_min, lon_max, lat_step, lon_step)
        self.classify_land_water()

    def create_grid(self, lat_min, lat_max, lon_min, lon_max, lat_step, lon_step):
        logging.debug("Creating grid...")
        latitudes = np.arange(lat_min, lat_max, lat_step)
        longitudes = np.arange(lon_min, lon_max, lon_step)
        grid = np.transpose([np.tile(longitudes, len(latitudes)), np.repeat(latitudes, len(longitudes))])
        grid_df = pd.DataFrame(grid, columns=['longitude', 'latitude'])
        grid_df['geometry'] = grid_df.apply(lambda x: Point(round(x.longitude, 3), round(x.latitude, 3)), axis=1)
        # Convert the DataFrame to a GeoDataFrame
        grid_gdf = gpd.GeoDataFrame(grid_df, geometry='geometry', crs="EPSG:4326")
        return grid_gdf

    def classify_land_water(self, chunk_size=1000):
        total_points = len(self.grid_df)
        num_chunks = (total_points // chunk_size) + 1
        logging.debug(f"Classifying land and water in {num_chunks} chunks...")

        # Initialize an empty Series to store results
        is_land_series = pd.Series(False, index=self.grid_df.index)

        for i in range(num_chunks):
            # Calculate the range for the current chunk
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size
            current_chunk = self.grid_df.iloc[start_idx:end_idx]

            # Perform the spatial join with the current chunk
            points_within_land = gpd.sjoin(current_chunk, self.land, how='inner', predicate='intersects')

            # Update the is_land Series with the results
            is_land_series.loc[points_within_land.index] = True

            # Report progress
            progress = ((i + 1) / num_chunks) * 100
            logging.debug(f"Chunk {i + 1} of {num_chunks} processed ({progress:.2f}% complete)")

        # Assign the results to the grid DataFrame
        self.grid_df['is_land'] = is_land_series
        self.grid_df['is_water'] = ~is_land_series

    def save_grid(self, file_name, folder_path):
        logging.debug("Saving grid to file...")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'wb') as file:
            pickle.dump(self.grid_df, file, pickle.HIGHEST_PROTOCOL)
        logging.debug("Grid saved to: {}".format(file_path))

# Usage:
if __name__ == "__main__":
    LAT_STEP, LON_STEP = 0.1, 0.1
    LAT_MIN, LAT_MAX = -60, 83
    LON_MIN, LON_MAX = -180, 180
    land_data_path = "data/geopackages/ne_10m_land.gpkg"

    logging.debug("Starting program...")
    grid_map = GridMap(land_data_path, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, LAT_STEP, LON_STEP)

    sea_grid = grid_map.grid_df[grid_map.grid_df['is_water']]
    logging.debug("Total number of sea grid points: {}".format(len(sea_grid)))

    grid_map.save_grid('sea_grid.pkl', 'grid_map')
    logging.debug("Program finished.")
