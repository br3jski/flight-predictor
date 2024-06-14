import csv
from collections import defaultdict
from prettytable import PrettyTable, ALL

def find_callsigns_with_multiple_airports(filename='data.csv', encoding='utf-8'):
    callsign_to_airports = defaultdict(lambda: {'climbing': [], 'descending': []})
    seen_records = set()
    
    try:
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
        
        table = PrettyTable()
        table.field_names = ["Callsign", "From", "From (ICAO)", "To", "To (ICAO)"]
        table.hrules = ALL  # Dodanie linii oddzielających wiersze
        
        record_count = 0
        
        for callsign, airports in callsign_to_airports.items():
            climbing_airports = airports['climbing']
            descending_airports = airports['descending']
            
            if climbing_airports and descending_airports:
                # Sprawdzamy, czy lotniska są różne
                for from_airport, from_icao in climbing_airports:
                    for to_airport, to_icao in descending_airports:
                        if from_airport != to_airport:
                            record_tuple = (callsign, from_airport, from_icao, to_airport, to_icao)
                            
                            if record_tuple not in seen_records:
                                table.add_row([callsign, from_airport, from_icao, to_airport, to_icao])
                                seen_records.add(record_tuple)
                                record_count += 1
        
        print(table)
        print(f"Total records: {record_count}")
    
    except FileNotFoundError:
        print(f"File {filename} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    find_callsigns_with_multiple_airports()