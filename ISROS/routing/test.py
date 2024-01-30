import geopandas as gpd
import matplotlib.pyplot as plt

sea_path = "E:/Programming in Python/applications/Thesis/ISROS/routing/data/ne_10m_ocean.shp"

gdf = gpd.read_file(sea_path)


gdf.plot()
print("Plot generated")
plt.savefig("E:/Programming in Python/applications/Thesis/ISROS/routing/data/plots/test.png")