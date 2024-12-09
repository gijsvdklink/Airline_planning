import pandas as pd

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
