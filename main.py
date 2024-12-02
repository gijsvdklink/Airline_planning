import sys
import os
import pandas as pd

# Voeg de hoofdmap (Airline_planning) toe aan sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.file_utils import load_excel
from utils.distance_calculations import calculate_distance
from models.demand_forecast import prepare_gravity_data, calibrate_gravity_model

# Laad de volledige dataset zonder header
demand_data = load_excel("data/DemandGroup16.xlsx", header=None)

# Extraheer coördinaten en ICAO-code
# Gebruik .loc in plaats van .iloc voor duidelijkheid en robuustheid
coordinates = demand_data.loc[4:6].transpose()  # Transponeer voor de juiste kolomindeling

# Pas de kolomnamen van de getransponeerde DataFrame aan
coordinates.columns = ['ICAO', 'Latitude', 'Longitude']

# Zorg dat de indexwaarden correct worden ingesteld op basis van ICAO-codes
coordinates.set_index('ICAO', inplace=True)
coordinates.index = coordinates.index.astype(str)

print("Coordinaten:")
print(coordinates.head())  # Controleer de coördinaten

# Extraheer vraagdata
demand_matrix = demand_data.iloc[13:, 1:]
demand_matrix.columns = demand_data.iloc[12, 1:]  # Kolommen zijn ICAO-codes
demand_matrix.index = demand_data.iloc[13:, 0]    # Rijen zijn ICAO-codes

# Vul ontbrekende namen in de vraagdata in
demand_matrix.index = demand_matrix.index.to_series().ffill()  # Vul ontbrekende rijnamen op basis van de vorige waarde
demand_matrix.columns = demand_matrix.columns.to_series().ffill()  # Vul ontbrekende kolomnamen op basis van de vorige waarde

# Verwijder eventuele niet-numerieke waarden uit de vraagdata
demand_matrix.replace('-', 0, inplace=True)
demand_matrix = demand_matrix.apply(pd.to_numeric, errors='coerce').fillna(0)

print("Vraagdata:")
print(demand_matrix.head())  # Controleer de vraagdata

# Voeg afstanden toe aan de dataset
def add_distances_to_data(demand_matrix, coordinates):
    distances = []
    for origin in demand_matrix.index:
        for destination in demand_matrix.columns:
            if origin != destination:
                lat1, lon1 = coordinates.loc[origin, 'Latitude'], coordinates.loc[origin, 'Longitude']
                lat2, lon2 = coordinates.loc[destination, 'Latitude'], coordinates.loc[destination, 'Longitude']
                distance = calculate_distance(lat1, lon1, lat2, lon2)
            else:
                distance = 0  # Afstand naar hetzelfde vliegveld is 0
            distances.append([origin, destination, distance])
    
    distance_df = pd.DataFrame(distances, columns=['Origin', 'Destination', 'Distance'])
    return distance_df

# Bereken de afstanden
distance_data = add_distances_to_data(demand_matrix, coordinates)
print("Afstanden:")
print(distance_data.head())  # Controleer de berekende afstanden

# Je kunt nu verdergaan met het voorbereiden van de data en het kalibreren van het model
# Bijvoorbeeld:
# demand_data_prepared = prepare_gravity_data(demand_matrix, distance_data)
# k, b1, b2, b3 = calibrate_gravity_model(demand_data_prepared)
# print(f"Gekalibreerde parameters: k={k}, b1={b1}, b2={b2}, b3={b3}")
