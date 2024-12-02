# demand_forecast.py
import pandas as pd
import numpy as np
import statsmodels.api as sm

def load_data():
    # Load population and GDP data from `pop.xlsx`, skipping rows before the actual headers
    pop_data = pd.read_excel('data/pop.xlsx', sheet_name=0, header=2)  # Header is in row 3 (index 2)
    
    # Print the first few rows to debug and verify
    print("Preview of pop_data (first few rows):")
    print(pop_data.head())

    # Select the relevant columns
    pop_data = pop_data[['City', '2020', '2023', 'Country', '2020.1', '2023.1']]
    pop_data.columns = ['City', 'Population_2020', 'Population_2023', 'Country', 'GDP_2020', 'GDP_2023']

    # Print column names after adjustment
    print("Columns in pop_data after adjustment:", pop_data.columns)

    # Load demand data from `DemandGroup16.xlsx`
    print("Loading demand data...")
    demand_data = pd.read_excel('data/DemandGroup16.xlsx', sheet_name=0)

    # Extract demand per week, starting from row 13
    print("Extracting demand data...")
    demand_per_week = demand_data.iloc[12:]  # Since data starts at row 13 (index 12)

    # Rename columns to make them easier to work with
    demand_per_week.columns = demand_data.iloc[11]  # The actual header is in row 12
    demand_per_week = demand_per_week.dropna(axis=1, how='all')  # Drop empty columns

    return pop_data, demand_per_week

def calibrate_gravity_model(pop_data, demand_data):
    # Filter data for 2020
    pop_2020 = pop_data[pop_data['Population_2020'].notna()]
    demand_2020 = demand_data[['Origin', 'Destination', 'Demand_2020']]

    # Merge dataframes to get population, GDP, and demand for corresponding origin and destination
    merged_data = pd.merge(demand_2020, pop_2020, left_on='Origin', right_on='City', suffixes=('_origin', '_dest'))
    merged_data = pd.merge(merged_data, pop_2020, left_on='Destination', right_on='City', suffixes=('_origin', '_dest'))

    # Apply logarithms to linearize
    merged_data['Log_Population'] = np.log(merged_data['Population_2020_origin'] * merged_data['Population_2020_dest'])
    merged_data['Log_GDP'] = np.log(merged_data['GDP_2020_origin'] * merged_data['GDP_2020_dest'])
    merged_data['Log_Distance'] = np.log(merged_data['Distance'])  # Assuming distances are precomputed

    # Prepare input (independent) variables and target (dependent) variable
    X = merged_data[['Log_Population', 'Log_GDP', 'Log_Distance']]  # Independent variables
    X = sm.add_constant(X)  # Add intercept term to the model
    y = np.log(merged_data['Demand_2020'])  # Dependent variable (log of demand)

    # Fit the model using Ordinary Least Squares (OLS)
    model = sm.OLS(y, X).fit()
    print(model.summary())  # Print summary of the model to verify results

    return model.params  # Return the model parameters (coefficients)