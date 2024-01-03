import csv

def get_ports_from_csv(csv_filepath):
    ports = []
    with open(csv_filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            coordinates = (row['Latitude'], row['Longitude'])
            port_name = row['Main Port Name']
            
            ports.append((port_name, coordinates))
    return ports