import requests
import json
import time
import csv
import io
from prettytable import PrettyTable
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Promień Ziemi w kilometrach
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

def find_nearest_airport(lat, lon, airports):
    if lat is None or lon is None:
        return None, None
    nearest_airport = None
    min_distance = float('inf')
    for airport in airports:
        airport_lat, airport_lon = airport['lat'], airport['lon']
        distance = haversine(lat, lon, airport_lat, airport_lon)
        if distance < min_distance:
            min_distance = distance
            nearest_airport = airport
    return nearest_airport, min_distance

def process_data(data, airports, csv_file_path):
    if 'acList' not in data:
        return

    callsigns = {}
    for entry in data['acList']:
        callsign = entry.get('Call', '')
        if callsign and not callsign.startswith("TXLU"):
            if callsign not in callsigns:
                callsigns[callsign] = entry

    rows = []
    for callsign, frame in callsigns.items():
        alt = frame.get('Alt')
        if alt is not None and alt >= 3000:
            alt = None

        vsi = frame.get('Vsi', 0)
        direction = 'climbing' if vsi > 0 else 'descending'

        lat = frame.get('Lat')
        long = frame.get('Long')

        if alt is not None and lat is not None and long is not None:
            nearest_airport, distance = find_nearest_airport(lat, long, airports)
            if distance is not None and distance <= 10:
                row = [callsign, "first", "GND" if alt == 0 else alt, vsi, lat, long, direction, nearest_airport['name'] if nearest_airport else 'N/A', nearest_airport['icao'] if nearest_airport else 'N/A', round(distance, 2) if distance else 'N/A']
                rows.append(row)

    # Dodanie danych do pliku CSV bez ponownego zapisywania nagłówków
    with open(csv_file_path, mode='a', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(rows)

def main():
    url = "http://virtualradar.nl/virtualradar/aircraftlist.json"
    interval = 30  # Interwał w sekundach

    # Przykładowa baza danych lotnisk
    airports = [
        # Airports - Poland
        {"name": "Chopin Airport", "icao": "EPWA", "lat": 52.1657, "lon": 20.9671},
        {"name": "Modlin Airport", "icao": "EPMO", "lat": 52.4511, "lon": 20.6518},
        # more airports
    ]


    # Inicjalizacja pliku CSV i zapisanie nagłówków tylko raz
    csv_file_path = 'data.csv'
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(["callsign", "frame", "Alt", "Vsi", "Lat", "Long", "Direction", "NearestArpt", "ICAO", "DistanceInKm"])

    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Zgłasza wyjątek, jeśli status odpowiedzi jest różny od 200 OK
            data = response.json()  # Parsowanie całej odpowiedzi jako JSON
            process_data(data, airports, csv_file_path)
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while fetching data: {e}")
        except json.JSONDecodeError as e:
            print(f"Error occurred while parsing JSON: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        
        time.sleep(interval)

if __name__ == "__main__":
    main()