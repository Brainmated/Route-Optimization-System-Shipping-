import csv
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_filepath = os.path.join(script_dir, "data", "ports.csv")

def parse_ports():
    ports = []

    with open(csv_filepath, mode = "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)

        for row in reader:
            port_name = row[3].strip()
            lat = row[30].strip()
            lon = row[31].strip()
            ports.append({"name": port_name, "latitude": lat, "longitude": lon})

    return ports

    