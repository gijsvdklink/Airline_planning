import sys
import os

# Add the parent directory of `models` to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np

# Path to the Excel file
data_file_path = 'data/DemandGroup16.xlsx'

# Load the airport_data sheet (skipping irrelevant rows)
airport_data = pd.read_excel(data_file_path, sheet_name='airport_data', header=None, usecols=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21])  # Include the desired columns

# Transpose the airport_data
airport_data_transposed = airport_data.transpose()

# Set the first row as the column headers
airport_data_transposed.columns = airport_data_transposed.iloc[0]

# Drop the first row (it’s now redundant)
airport_data_transposed = airport_data_transposed[1:]

# Load demand_per_week sheet with all rows
demand_per_week = pd.read_excel(data_file_path, sheet_name='demand_per_week', header=None, usecols=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21])

# Clean demand_per_week
demand_per_week.columns = demand_per_week.iloc[0]  # First row becomes column names
demand_per_week = demand_per_week[1:]  # Exclude the first row from the data
demand_per_week.index = demand_per_week.iloc[:, 0]  # First column becomes row index (origin airports)
demand_per_week = demand_per_week.iloc[:, 1:]  # Exclude the first column from data
demand_per_week = demand_per_week.apply(pd.to_numeric, errors='coerce')  # Convert values to numeric

# Load the population and GDP data
pop_data = pd.read_excel('data/pop.xlsx', usecols=[0, 1, 2, 4, 5, 6], skiprows=[0, 1])

# Convert Population and GDP columns to numeric in-place
pop_data[2020] = pd.to_numeric(pop_data[2020], errors='coerce')
pop_data[2023] = pd.to_numeric(pop_data[2023], errors='coerce')
pop_data['2020.1'] = pd.to_numeric(pop_data['2020.1'], errors='coerce')
pop_data['2023.1'] = pd.to_numeric(pop_data['2023.1'], errors='coerce')

# Preview the cleaned data
print("\nCleaned Population and GDP Data:")
print(pop_data)
print("\nCleaned Transposed Airport Data:")
print(airport_data_transposed)
print("\nCleaned Demand Per Week Data:")
print(demand_per_week)

import sys


from utils.distance_calculations import calculate_distance, calculate_distance_matrix

# Extract latitudes and longitudes
latitudes = airport_data_transposed['Latitude (deg)'].astype(float).values
longitudes = airport_data_transposed['Longitude (deg)'].astype(float).values

# Extract city names (using the ICAO Code column)
city_names = airport_data_transposed['ICAO Code'].tolist()

# Calculate the distance matrix using the imported function
distance_matrix = calculate_distance_matrix(latitudes, longitudes)

# Convert the distance matrix to a DataFrame with city names as both row and column headers
distance_df = pd.DataFrame(distance_matrix, index=city_names, columns=city_names)

# Round the values to one decimal place
distance_df = distance_df.round(1)

# Print the full distance matrix
print("\nDistance Matrix with City Names:")
print(distance_df)

# Save the full distance matrix to a CSV file
distance_df.to_csv('distance_matrix_with_city_names.csv', index=True)

# Print only distances from Frankfurt (EDDF)
print("\nDistances from Frankfurt (EDDF):")
if "EDDF" in city_names:
    distances_from_frankfurt = distance_df.loc["EDDF"]  # Extract row for Frankfurt
    print(distances_from_frankfurt)
    
    # Save Frankfurt distances to a separate CSV
    distances_from_frankfurt.to_csv('distances_from_frankfurt.csv', header=True)
else:
    print("Frankfurt (EDDF) not found in city names.")



    