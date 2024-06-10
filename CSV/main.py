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

def process_data(data, airports):
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
    with open(csv_file_path, mode='a', newline='') as file:
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
        {"name": "Gdańsk Airport", "icao": "EPGD", "lat": 54.3776, "lon": 18.4662},
        {"name": "Kraków Airport", "icao": "EPKK", "lat": 50.0777, "lon": 19.7848},
        {"name": "Wrocław Airport", "icao": "EPWR", "lat": 51.1027, "lon": 16.8858},
        {"name": "Poznań Airport", "icao": "EPPO", "lat": 52.421, "lon": 16.8263},
        {"name": "Katowice Airport", "icao": "EPKT", "lat": 50.4743, "lon": 19.08},
        {"name": "Łódź Airport", "icao": "EPLL", "lat": 51.7219, "lon": 19.3981},
        {"name": "Rzeszów Airport", "icao": "EPRZ", "lat": 50.1109, "lon": 22.018},
        {"name": "Szczecin Airport", "icao": "EPSC", "lat": 53.5847, "lon": 14.9022},
        {"name": "Bydgoszcz Airport", "icao": "EPBY", "lat": 53.0968, "lon": 17.9779},
        {"name": "Lublin Airport", "icao": "EPLB", "lat": 51.2403, "lon": 22.7137},
        {"name": "Olsztyn Airport", "icao": "EPSY", "lat": 53.4817, "lon": 20.9372},
        {"name": "Zielona Góra Airport", "icao": "EPZG", "lat": 52.1385, "lon": 15.7986},
        {"name": "Radom Airport", "icao": "EPRA", "lat": 51.3894, "lon": 21.2131},

        #Airports - Germany
        {"name": "Berlin Brandenburg Airport", "icao": "EDDB", "lat": 52.3667, "lon": 13.5033},
        {"name": "Frankfurt Airport", "icao": "EDDF", "lat": 50.0333, "lon": 8.5706},
        {"name": "Munich Airport", "icao": "EDDM", "lat": 48.3537, "lon": 11.775},
        {"name": "Düsseldorf Airport", "icao": "EDDL", "lat": 51.2807, "lon": 6.7575},
        {"name": "Hamburg Airport", "icao": "EDDH", "lat": 53.6303, "lon": 9.9882},
        {"name": "Cologne Bonn Airport", "icao": "EDDK", "lat": 50.8659, "lon": 7.1427},
        {"name": "Stuttgart Airport", "icao": "EDDS", "lat": 48.6899, "lon": 9.2210},
        {"name": "Hannover Airport", "icao": "EDDV", "lat": 52.4611, "lon": 9.6856},
        {"name": "Nuremberg Airport", "icao": "EDDN", "lat": 49.4987, "lon": 11.0669},
        {"name": "Leipzig/Halle Airport", "icao": "EDDP", "lat": 51.4239, "lon": 12.2364},
        {"name": "Bremen Airport", "icao": "EDDW", "lat": 53.0475, "lon": 8.7867},
        {"name": "Hahn Airport", "icao": "EDFH", "lat": 49.9487, "lon": 7.2639},
        {"name": "Dresden Airport", "icao": "EDDC", "lat": 51.1328, "lon": 13.7672},
        {"name": "Münster Osnabrück Airport", "icao": "EDDG", "lat": 52.1346, "lon": 7.6848},
        {"name": "Memmingen Airport", "icao": "EDJA", "lat": 47.9888, "lon": 10.2395},

        # Airports - Benelux
        {"name": "Amsterdam Airport Schiphol", "icao": "EHAM", "lat": 52.3086, "lon": 4.7639},
        {"name": "Brussels Airport", "icao": "EBBR", "lat": 50.9014, "lon": 4.4844},
        {"name": "Antwerp International Airport", "icao": "EBAW", "lat": 51.1894, "lon": 4.4603},
        {"name": "Rotterdam The Hague Airport", "icao": "EHRD", "lat": 51.9569, "lon": 4.4372},
        {"name": "Eindhoven Airport", "icao": "EHEH", "lat": 51.4501, "lon": 5.3743},
        {"name": "Maastricht Aachen Airport", "icao": "EHBK", "lat": 50.9117, "lon": 5.7706},
        {"name": "Groningen Airport Eelde", "icao": "EHGG", "lat": 53.1197, "lon": 6.5794},
        {"name": "Liege Airport", "icao": "EBLG", "lat": 50.6374, "lon": 5.4432},
        {"name": "Ostend-Bruges International Airport", "icao": "EBOS", "lat": 51.1989, "lon": 2.8622},
        {"name": "Charleroi Airport", "icao": "EBCI", "lat": 50.4592, "lon": 4.4531},

        # Airports - Czech Republic, Slovakia, Austria
        {"name": "Václav Havel Airport Prague", "icao": "LKPR", "lat": 50.1008, "lon": 14.26},
        {"name": "Brno-Tuřany Airport", "icao": "LKTB", "lat": 49.1513, "lon": 16.6944},
        {"name": "Ostrava Leos Janacek Airport", "icao": "LKMT", "lat": 49.6962, "lon": 18.1111},
        {"name": "Karlovy Vary Airport", "icao": "LKKV", "lat": 50.2025, "lon": 12.9142},
        {"name": "Pardubice Airport", "icao": "LKPD", "lat": 50.0134, "lon": 15.7386},
        {"name": "Košice International Airport", "icao": "LZKZ", "lat": 48.6631, "lon": 21.2411},
        {"name": "M. R. Štefánik Airport", "icao": "LZIB", "lat": 48.1702, "lon": 17.2127},
        {"name": "Vienna International Airport", "icao": "LOWW", "lat": 48.1102, "lon": 16.5697},
        {"name": "Graz Airport", "icao": "LOWG", "lat": 46.9911, "lon": 15.4392},
        {"name": "Linz Airport", "icao": "LOWL", "lat": 48.2332, "lon": 14.1872},
        {"name": "Salzburg Airport", "icao": "LOWS", "lat": 47.7933, "lon": 13.0043},
        {"name": "Innsbruck Airport", "icao": "LOWI", "lat": 47.2602, "lon": 11.344},
        {"name": "Klagenfurt Airport", "icao": "LOWK", "lat": 46.6425, "lon": 14.3378},
        {"name": "Linz Airport", "icao": "LOWL", "lat": 48.2332, "lon": 14.1872},
        {"name": "Salzburg Airport", "icao": "LOWS", "lat": 47.7933, "lon": 13.0043},
        {"name": "Innsbruck Airport", "icao": "LOWI", "lat": 47.2602, "lon": 11.344},
        {"name": "Klagenfurt Airport", "icao": "LOWK", "lat": 46.6425, "lon": 14.3378},

        # Airports - France and UK (including Ireland)
        {"name": "Paris Charles de Gaulle Airport", "icao": "LFPG", "lat": 49.0097, "lon": 2.5478},
        {"name": "Paris Orly Airport", "icao": "LFPO", "lat": 48.7262, "lon": 2.3659},
        {"name": "Nice Côte d'Azur Airport", "icao": "LFMN", "lat": 43.6584, "lon": 7.2159},
        {"name": "Lyon-Saint Exupéry Airport", "icao": "LFLL", "lat": 45.7256, "lon": 5.0811},
        {"name": "Marseille Provence Airport", "icao": "LFML", "lat": 43.4393, "lon": 5.2214},
        {"name": "Toulouse-Blagnac Airport", "icao": "LFBO", "lat": 43.6545, "lon": 1.2446},
        {"name": "Bordeaux-Mérignac Airport", "icao": "LFBD", "lat": 44.8283, "lon": -0.7156},
        {"name": "Nantes Atlantique Airport", "icao": "LFRS", "lat": 47.1569, "lon": -1.6106},
        {"name": "Lille Airport", "icao": "LFQQ", "lat": 50.5706, "lon": 3.1061},
        {"name": "Strasbourg Airport", "icao": "LFST", "lat": 48.5383, "lon": 7.6281},
        {"name": "Belfast International Airport", "icao": "EGAA", "lat": 54.6575, "lon": -6.2158},
        {"name": "Belfast City Airport", "icao": "EGAC", "lat": 54.6181, "lon": -5.8725},
        {"name": "Dublin Airport", "icao": "EIDW", "lat": 53.4213, "lon": -6.2701},
        {"name": "Shannon Airport", "icao": "EINN", "lat": 52.7019, "lon": -8.9248},
        {"name": "Cork Airport", "icao": "EICK", "lat": 51.8413, "lon": -8.4911},
        {"name": "Edinburgh Airport", "icao": "EGPH", "lat": 55.9508, "lon": -3.3615},
        {"name": "Glasgow Airport", "icao": "EGPF", "lat": 55.8642, "lon": -4.4331},
        {"name": "Manchester Airport", "icao": "EGCC", "lat": 53.3651, "lon": -2.2728},
        {"name": "London Heathrow Airport", "icao": "EGLL", "lat": 51.4700, "lon": -0.4543},
        {"name": "London Gatwick Airport", "icao": "EGKK", "lat": 51.1537, "lon": -0.1821},
        {"name": "London Stansted Airport", "icao": "EGSS", "lat": 51.8850, "lon": 0.2350},
        {"name": "London Luton Airport", "icao": "EGGW", "lat": 51.8747, "lon": -0.3683},
        {"name": "London City Airport", "icao": "EGLC", "lat": 51.5053, "lon": 0.0553},
        {"name": "Birmingham Airport", "icao": "EGBB", "lat": 52.4539, "lon": -1.7480},
        {"name": "Bristol Airport", "icao": "EGGD", "lat": 51.3827, "lon": -2.7191},
        {"name": "Newcastle Airport", "icao": "EGNT", "lat": 55.0375, "lon": -1.6917},
        {"name": "Leeds Bradford Airport", "icao": "EGNM", "lat": 53.8697, "lon": -1.6606},
        {"name": "Liverpool John Lennon Airport", "icao": "EGGP", "lat": 53.3336, "lon": -2.8497},
        {"name": "Glasgow Prestwick Airport", "icao": "EGPK", "lat": 55.5094, "lon": -4.6117},
        {"name": "Aberdeen International Airport", "icao": "EGPD", "lat": 57.2019, "lon": -2.1978},
        {"name": "Southampton Airport", "icao": "EGHI", "lat": 50.9503, "lon": -1.3569},
        {"name": "Cardiff Airport", "icao": "EGFF", "lat": 51.3967, "lon": -3.3433},
        {"name": "Exeter Airport", "icao": "EGTE", "lat": 50.7344, "lon": -3.4139},
        {"name": "East Midlands Airport", "icao": "EGNX", "lat": 52.8306, "lon": -1.3281},
        {"name": "Norwich Airport", "icao": "EGSH", "lat": 52.6758, "lon": 1.2828},
        {"name": "Jersey Airport", "icao": "EGJJ", "lat": 49.2075, "lon": -2.1953},
        {"name": "Guernsey Airport", "icao": "EGJB", "lat": 49.4349, "lon": -2.6010},
        {"name": "Isle of Man Airport", "icao": "EGNS", "lat": 54.0833, "lon": -4.6239},
        {"name": "Newquay Cornwall Airport", "icao": "EGHQ", "lat": 50.4406, "lon": -4.9958},
        {"name": "Inverness Airport", "icao": "EGPE", "lat": 57.5394, "lon": -4.0633},
        {"name": "Derry Airport", "icao": "EGAE", "lat": 55.0428, "lon": -7.1611},
        {"name": "George Best Belfast City Airport", "icao": "EGAC", "lat": 54.6181, "lon": -5.8725},

        #Airports - Spain and Portugal
        {"name": "Adolfo Suárez Madrid–Barajas Airport", "icao": "LEMD", "lat": 40.4719, "lon": -3.5626},
        {"name": "Barcelona–El Prat Josep Tarradellas Airport", "icao": "LEBL", "lat": 41.2971, "lon": 2.0785},
        {"name": "Palma de Mallorca Airport", "icao": "LEPA", "lat": 39.5517, "lon": 2.7388},
        {"name": "Málaga Airport", "icao": "LEMG", "lat": 36.6749, "lon": -4.4991},
        {"name": "Alicante–Elche Airport", "icao": "LEAL", "lat": 38.2822, "lon": -0.5582},
        {"name": "Valencia Airport", "icao": "LEVC", "lat": 39.4914, "lon": -0.4733},
        {"name": "Seville Airport", "icao": "LEZL", "lat": 37.4179, "lon": -5.8931},
        {"name": "Bilbao Airport", "icao": "LEBB", "lat": 43.3017, "lon": -2.9106},
        {"name": "Tenerife South Airport", "icao": "GCTS", "lat": 28.0445, "lon": -16.5725},
        {"name": "Tenerife North Airport", "icao": "GCXO", "lat": 28.4827, "lon": -16.3415},
        {"name": "Gran Canaria Airport", "icao": "GCLP", "lat": 27.9319, "lon": -15.3866},
        {"name": "Lanzarote Airport", "icao": "GCRR", "lat": 28.9455, "lon": -13.6052},
        {"name": "Fuerteventura Airport", "icao": "GCFV", "lat": 28.4527, "lon": -13.8638},
        {"name": "La Gomera Airport", "icao": "GCGM", "lat": 28.0296, "lon": -17.2146},
        {"name": "Ibiza Airport", "icao": "LEIB", "lat": 38.8729, "lon": 1.3731},
        {"name": "Menorca Airport", "icao": "LEMH", "lat": 39.8626, "lon": 4.2186},
        {"name": "Madeira Airport", "icao": "LPMA", "lat": 32.6979, "lon": -16.7745},
        {"name": "Faro Airport", "icao": "LPFR", "lat": 37.0144, "lon": -7.9659},
        {"name": "Porto Airport", "icao": "LPPR", "lat": 41.2371, "lon": -8.6702},
        {"name": "Lisbon Portela Airport", "icao": "LPPT", "lat": 38.7742, "lon": -9.1342},
        {"name": "Funchal Airport", "icao": "LPMA", "lat": 32.6979, "lon": -16.7745},
        {"name": "Gibraltar International Airport", "icao": "LXGB", "lat": 36.1511, "lon": -5.3497},

        #Airports - Scandinavia
        # Airports - Scandinavia
        {"name": "Stockholm Arlanda Airport", "icao": "ESSA", "lat": 59.6519, "lon": 17.9186},
        {"name": "Copenhagen Airport", "icao": "EKCH", "lat": 55.6181, "lon": 12.6561},
        {"name": "Oslo Airport, Gardermoen", "icao": "ENGM", "lat": 60.1976, "lon": 11.1004},
        {"name": "Helsinki Airport", "icao": "EFHK", "lat": 60.3172, "lon": 24.9633},
        {"name": "Gothenburg Landvetter Airport", "icao": "ESGG", "lat": 57.6686, "lon": 12.2922},
        {"name": "Bergen Airport, Flesland", "icao": "ENBR", "lat": 60.2936, "lon": 5.2181},
        {"name": "Stavanger Airport, Sola", "icao": "ENZV", "lat": 58.8804, "lon": 5.6319},
        {"name": "Trondheim Airport, Værnes", "icao": "ENVA", "lat": 63.4575, "lon": 10.9242},
        {"name": "Tromsø Airport, Langnes", "icao": "ENTC", "lat": 69.6833, "lon": 18.9189},
        {"name": "Bodø Airport", "icao": "ENBO", "lat": 67.2692, "lon": 14.3653},
        {"name": "Kiruna Airport", "icao": "ESNQ", "lat": 67.8219, "lon": 20.3369},
        {"name": "Luleå Airport", "icao": "ESPA", "lat": 65.5436, "lon": 22.1225},
        {"name": "Umeå Airport", "icao": "ESNU", "lat": 63.7917, "lon": 20.2828},
        {"name": "Oulu Airport", "icao": "EFOU", "lat": 64.9301, "lon": 25.3541},
        {"name": "Tampere-Pirkkala Airport", "icao": "EFTP", "lat": 61.4142, "lon": 23.6044},
        {"name": "Turku Airport", "icao": "EFTU", "lat": 60.5142, "lon": 22.2628},
        {"name": "Vaasa Airport", "icao": "EFVA", "lat": 63.0507, "lon": 21.7622},
        {"name": "Reykjavík Keflavík Airport", "icao": "BIKF", "lat": 63.9850, "lon": -22.6056},
        {"name": "Nuuk Airport", "icao": "BGGH", "lat": 64.1900, "lon": -51.6781},
        {"name": "Ilulissat Airport", "icao": "BGJN", "lat": 69.2433, "lon": -51.0572},
        {"name": "Narsarsuaq Airport", "icao": "BGBW", "lat": 61.1605, "lon": -45.4250},
        {"name": "Sisimiut Airport", "icao": "BGSS", "lat": 66.9514, "lon": -53.7297},
        {"name": "Aasiaat Airport", "icao": "BGAA", "lat": 68.7217, "lon": -52.7847},
        {"name": "Qaqortoq Heliport", "icao": "BGJH", "lat": 60.7153, "lon": -46.0297},
        {"name": "Longyearbyen Airport", "icao": "ENSB", "lat": 78.2461, "lon": 15.4656},
        {"name": "Tórshavn Vágar Airport", "icao": "EKVG", "lat": 62.0636, "lon": -7.2772},
        {"name": "Svalbard Airport, Longyear", "icao": "ENSB", "lat": 78.2461, "lon": 15.4656},
        {"name": "Faroe Islands Vágar Airport", "icao": "EKVG", "lat": 62.0636, "lon": -7.2772},
        {"name": "Greenland Narsarsuaq Airport", "icao": "BGBW", "lat": 61.1605, "lon": -45.4250},
        {"name": "Greenland Sisimiut Airport", "icao": "BGSS", "lat": 66.9514, "lon": -53.7297},
        {"name": "Greenland Aasiaat Airport", "icao": "BGAA", "lat": 68.7217, "lon": -52.7847},
        {"name": "Greenland Qaqortoq Heliport", "icao": "BGJH", "lat": 60.7153, "lon": -46.0297}
    ]


    # Inicjalizacja pliku CSV i zapisanie nagłówków tylko raz
    csv_file_path = 'data.csv'
    with open(csv_file_path, mode='w', newline='') as file:
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