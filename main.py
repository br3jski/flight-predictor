import requests
import json
import time
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

def process_data(data, airports):
    if 'acList' not in data:
        return

    callsigns = {}
    for entry in data['acList']:
        callsign = entry.get('Call', '')
        if callsign and not callsign.startswith("TXLU"):
            if callsign not in callsigns:
                callsigns[callsign] = {'first': entry, 'last': entry}
            else:
                callsigns[callsign]['last'] = entry

    table = PrettyTable()
    table.field_names = ["callsign", "frame", "Alt", "Vsi", "Lat", "Long", "Direction", "Nearest Airport", "Distance (km)"]

    for callsign, frames in callsigns.items():
        first_frame = frames['first']
        last_frame = frames['last']

        first_alt = first_frame.get('Alt')
        last_alt = last_frame.get('Alt')

        if first_alt is not None and first_alt >= 3000:
            first_alt = None
        if last_alt is not None and last_alt >= 3000:
            last_alt = None

        first_vsi = first_frame.get('Vsi', 0)
        last_vsi = last_frame.get('Vsi', 0)

        first_direction = 'climbing' if first_vsi > 0 else 'descending'
        last_direction = 'climbing' if last_vsi > 0 else 'descending'

        first_lat = first_frame.get('Lat')
        first_long = first_frame.get('Long')
        last_lat = last_frame.get('Lat')
        last_long = last_frame.get('Long')

        if first_alt is not None and first_lat is not None and first_long is not None:
            nearest_airport, distance = find_nearest_airport(first_lat, first_long, airports)
            if distance is not None and distance <= 10:
                table.add_row([callsign, "first", "GND" if first_alt == 0 else first_alt, first_vsi, first_lat, first_long, first_direction, nearest_airport['name'] if nearest_airport else 'N/A', round(distance, 2) if distance else 'N/A'])
        if last_alt is not None and last_lat is not None and last_long is not None:
            nearest_airport, distance = find_nearest_airport(last_lat, last_long, airports)
            if distance is not None and distance <= 10:
                table.add_row([callsign, "last", "GND" if last_alt == 0 else last_alt, last_vsi, last_lat, last_long, last_direction, nearest_airport['name'] if nearest_airport else 'N/A', round(distance, 2) if distance else 'N/A'])

    print(table)

def main():
    url = "http://virtualradar.nl/virtualradar/aircraftlist.json"
    interval = 10  # Interwał w sekundach

    # Przykładowa baza danych lotnisk
    airports = [
        {"name": "Chopin Airport", "lat": 52.1657, "lon": 20.9671},
        {"name": "John Paul II Airport", "lat": 50.0777, "lon": 19.7848},
        {"name": "Gdańsk Lech Wałęsa Airport", "lat": 54.3776, "lon": 18.4662},
        {"name": "Wrocław Nicolaus Copernicus Airport", "lat": 51.1027, "lon": 16.8858},
        {"name": "Kraków Airport", "lat": 50.0777, "lon": 19.7848},
        {"name": "Poznań-Ławica Airport", "lat": 52.421, "lon": 16.8263},
        {"name": "Szczecin-Goleniów Airport", "lat": 53.5847, "lon": 14.9022},
        {"name": "Bydgoszcz Ignacy Jan Paderewski Airport", "lat": 53.0968, "lon": 17.9779},
        {"name": "Lublin Airport", "lat": 51.2403, "lon": 22.7137},
        {"name": "Rzeszów-Jasionka Airport", "lat": 50.1109, "lon": 22.018},
        {"name": "Katowice Airport", "lat": 50.4743, "lon": 19.0808},
        {"name": "Łódź Władysław Reymont Airport", "lat": 51.7211, "lon": 19.3981},
        {"name": "Olsztyn-Mazury Airport", "lat": 53.7799, "lon": 20.4752},
        {"name": "Radom Airport", "lat": 51.3894, "lon": 21.2131},
        {"name": "Zielona Góra-Babimost Airport", "lat": 52.1385, "lon": 15.7986},
        {"name": "Modlin Airport", "lat": 52.4511, "lon": 20.6518},
        #DE
        {"name": "Berlin Brandenburg Airport", "lat": 52.3667, "lon": 13.5033},
        {"name": "Frankfurt Airport", "lat": 50.0333, "lon": 8.5706},
        {"name": "Dresden Airport", "lat": 51.1325, "lon": 13.7672},
        {"name": "Hamburg Airport", "lat": 53.6303, "lon": 9.9882},
        {"name": "Munich Airport", "lat": 48.3537, "lon": 11.7861},
        {"name": "Stuttgart Airport", "lat": 48.6899, "lon": 9.221},
        {"name": "Düsseldorf Airport", "lat": 51.2808, "lon": 6.7669},
        {"name": "Cologne Bonn Airport", "lat": 50.8789, "lon": 7.1204},
        {"name": "Hannover Airport", "lat": 52.4611, "lon": 9.6851},
        {"name": "Nuremberg Airport", "lat": 49.4987, "lon": 11.0781},
        {"name": "Leipzig/Halle Airport", "lat": 51.4239, "lon": 12.2364},
        {"name": "Bremen Airport", "lat": 53.0475, "lon": 8.7867},
        {"name": "Hahn Airport", "lat": 49.9487, "lon": 7.2639},
        {"name": "Münster Osnabrück Airport", "lat": 52.1346, "lon": 7.6847},
        {"name": "Karlsruhe/Baden-Baden Airport", "lat": 48.7794, "lon": 8.0805},
        {"name": "Dortmund Airport", "lat": 51.5183, "lon": 7.6122},
        {"name": "Saarbrücken Airport", "lat": 49.2147, "lon": 7.1095},
        {"name": "Paderborn Lippstadt Airport", "lat": 51.6141, "lon": 8.6163},
        {"name": "Memmingen Airport", "lat": 47.9888, "lon": 10.2395},
        {"name": "Friedrichshafen Airport", "lat": 47.6713, "lon": 9.5115},
        {"name": "Rostock-Laage Airport", "lat": 53.9182, "lon": 12.2783},
        {"name": "Erfurt-Weimar Airport", "lat": 50.9798, "lon": 10.9581},
        {"name": "Lübeck Airport", "lat": 53.8053, "lon": 10.7172},
        #NED/BEL
        {"name": "Schiphol Airport", "lat": 52.3086, "lon": 4.7639},
        {"name": "Eindhoven Airport", "lat": 51.4501, "lon": 5.3743},
        {"name": "Rotterdam The Hague Airport", "lat": 51.9569, "lon": 4.4372},
        {"name": "Maastricht Aachen Airport", "lat": 50.9117, "lon": 5.7706},
        {"name": "Groningen Airport Eelde", "lat": 53.1197, "lon": 6.5794},
        {"name": "Antwerp International Airport", "lat": 51.1894, "lon": 4.4603},
        {"name": "Brussels Airport", "lat": 50.9014, "lon": 4.4844},
        {"name": "Charleroi Airport", "lat": 50.4592, "lon": 4.453},
        {"name": "Liège Airport", "lat": 50.6374, "lon": 5.4431},
        {"name": "Ostend-Bruges International Airport", "lat": 51.1989, "lon": 2.8622},
        {"name": "Kortrijk-Wevelgem International Airport", "lat": 50.8172, "lon": 3.2047},
        #UK
        {"name": "Heathrow Airport", "lat": 51.4700, "lon": -0.4543},
        {"name": "Gatwick Airport", "lat": 51.1537, "lon": -0.1821},
        {"name": "Manchester Airport", "lat": 53.3653, "lon": -2.2724},
        {"name": "Stansted Airport", "lat": 51.8853, "lon": 0.2353},
        {"name": "Luton Airport", "lat": 51.8787, "lon": -0.3755},
        {"name": "Edinburgh Airport", "lat": 55.9500, "lon": -3.3725},
        {"name": "Birmingham Airport", "lat": 52.4539, "lon": -1.7480},
        {"name": "Glasgow Airport", "lat": 55.8642, "lon": -4.4330},
        {"name": "Bristol Airport", "lat": 51.3826, "lon": -2.7191},
        {"name": "Newcastle Airport", "lat": 55.0375, "lon": -1.6917},
        {"name": "Liverpool John Lennon Airport", "lat": 53.3336, "lon": -2.8497},
        {"name": "London City Airport", "lat": 51.5053, "lon": 0.0553},
        {"name": "Leeds Bradford Airport", "lat": 53.8659, "lon": -1.6604},
        {"name": "East Midlands Airport", "lat": 52.8258, "lon": -1.3325},
        {"name": "Aberdeen Airport", "lat": 57.2019, "lon": -2.1978},
        {"name": "Southampton Airport", "lat": 50.9503, "lon": -1.3567},
        {"name": "Dublin Airport", "lat": 53.4214, "lon": -6.2701},
        {"name": "Belfast International Airport", "lat": 54.6575, "lon": -6.2178},
        {"name": "Belfast City Airport", "lat": 54.6181, "lon": -5.8725},
        {"name": "Cardiff Airport", "lat": 51.3967, "lon": -3.3433}
    ]

    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Zgłasza wyjątek, jeśli status odpowiedzi jest różny od 200 OK
            data = response.json()  # Parsowanie całej odpowiedzi jako JSON
            process_data(data, airports)
            print("==========")
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while fetching data: {e}")
        except json.JSONDecodeError as e:
            print(f"Error occurred while parsing JSON: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        
        time.sleep(interval)

if __name__ == "__main__":
    main()