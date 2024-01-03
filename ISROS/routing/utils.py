import csv

def get_ports_from_csv(csv_filepath):
    ports = []
    with open(csv_filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ports.append((row['Main Port Name'], row['World Port Index Number']))
    return ports