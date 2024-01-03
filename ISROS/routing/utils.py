import csv

def get_ports_from_csv(csv_filepath):
    ports = []
    with open(csv_filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            lat = row['Latitude']
            lon = row['Longitude']
            port_name = row['Main Port Name']
            # Ensure that latitude and longitude are converted from string to float
            try:
                lat_float = float(lat)
                lon_float = float(lon)
            except ValueError as e:
                # Handle the exception if conversion fails
                print(f"Could not convert lat/lon to float for port {port_name}: {e}")
                continue  # Skip this row and move to the next

            # Append a tuple with all necessary information
            ports.append((port_name, lat_float, lon_float))
    return ports