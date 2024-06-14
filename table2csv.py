import csv
from collections import defaultdict
import time

def find_callsigns_with_multiple_airports(filename='data.csv', csv_output='output.csv', encoding='utf-8'):
    callsign_to_airports = defaultdict(lambda: {'climbing': [], 'descending': []})
    seen_records = set()
    last_update_time = 0 

    try:
        while True:
            current_time = time.time()
            if current_time - last_update_time >= 86400:
                with open(filename, mode='r', encoding=encoding) as file:
                    csv_reader = csv.DictReader(file)
                    
                    for row in csv_reader:
                        callsign = row['callsign']
                        nearest_arpt = row['NearestArpt']
                        icao = row['ICAO']
                        direction = row['Direction']
                        
                        if direction == 'climbing':
                            callsign_to_airports[callsign]['climbing'].append((nearest_arpt, icao))
                        elif direction == 'descending':
                            callsign_to_airports[callsign]['descending'].append((nearest_arpt, icao))

                new_records_count = 0  # Licznik nowych rekordów

                with open(csv_output, mode='a', newline='', encoding=encoding) as csvfile:
                    fieldnames = ["callsign", "dep_icao", "arr_icao"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    if csvfile.tell() == 0:
                        writer.writeheader()
                    for callsign, airports in callsign_to_airports.items():
                        climbing_airports = airports['climbing']
                        descending_airports = airports['descending']
                        
                        if climbing_airports and descending_airports:
                            for from_airport, from_icao in climbing_airports:
                                for to_airport, to_icao in descending_airports:
                                    if from_airport != to_airport:
                                        record_tuple = (callsign, from_airport, from_icao, to_airport, to_icao)
                                        
                                        if record_tuple not in seen_records:
                                            writer.writerow({"callsign": callsign, "dep_icao": from_icao, "arr_icao": to_icao})
                                            seen_records.add(record_tuple)
                                            new_records_count += 1
                                            
                print(f"Dodano {new_records_count} lotów")  # Komunikat o dodanych lotach

                seen_records.clear() 
                last_update_time = current_time

            time.sleep(60) 

    except FileNotFoundError:
        print(f"File {filename} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    find_callsigns_with_multiple_airports()
