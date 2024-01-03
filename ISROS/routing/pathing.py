import folium
from folium.plugins import AntPath

class Pathing:
    def __init__(self, location1, location2):
        self.location1 = location1
        self.location2 = location2

    def get_map(self):
        # Create a folium map object
        m = folium.Map(location=self.location1, zoom_start=12)

        # Add markers for the start and end points
        folium.Marker(self.location1, tooltip='Start').add_to(m)
        folium.Marker(self.location2, tooltip='End').add_to(m)

        # Draw a path between the two points
        AntPath(locations=[self.location1, self.location2]).add_to(m)

        return m