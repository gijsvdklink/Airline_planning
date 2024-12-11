import pandas as pd
import numpy as np
from gurobipy import Model, GRB, quicksum

# Load demand data (from assignment 1A)
demand_data = pd.read_excel('Future_Demand_2025_with_Gravity_Model.xlsx', index_col=0)

# Load aircraft data from Appendix D
aircraft_data = pd.DataFrame({
    'Type': ['Aircraft 1', 'Aircraft 2', 'Aircraft 3', 'Aircraft 4'],
    'Seats': [45, 70, 150, 320],
    'Max_Range': [1500, 3300, 6300, 12000],
    'Lease_Cost': [15000, 34000, 80000, 190000],
    'Fixed_Cost': [300, 600, 1250, 2000],
    'Time_Cost': [750, 775, 1400, 2800],
    'Fuel_Cost': [1.0, 2.0, 3.75, 9.0],
    'TAT': [25, 35, 45, 60],  # Turn-Around Time in minutes
    'Speed': [550, 820, 850, 870],  # Speed in km/h
    'Runway_Required': [1400, 1600, 1800, 2600]
})
aircraft_data.set_index('Type', inplace=True)

# Constants
HOURS_PER_DAY = 10
DAYS_PER_WEEK = 7
MAX_HOURS_PER_WEEK = HOURS_PER_DAY * DAYS_PER_WEEK
LOAD_FACTOR = 0.75  # Given in the assignment
FUEL_COST = 1.42  # EUR/gallon
ECONOMIES_OF_SCALE = 0.7  # 30% cost reduction at hub
HUB_AIRPORT = 'EHAM'  # Example hub airport code (Schiphol)

# Load distance data
distance_data = pd.read_csv('distance_matrix_with_city_names.csv', index_col=0)

# Ensure that demand_data and distance_data have the same indices
demand_data = demand_data.reindex(index=distance_data.index, columns=distance_data.columns)
demand_data.fillna(0, inplace=True)

# Create the model
model = Model("Network_Fleet_Optimization")

# Decision Variables
# Flight frequency between i and j with aircraft type k
flight_vars = model.addVars(
    demand_data.index, demand_data.columns, aircraft_data.index, vtype=GRB.INTEGER, name="FlightFrequency"
)

# Number of aircraft of type k
aircraft_vars = model.addVars(aircraft_data.index, vtype=GRB.INTEGER, name="NumAircraft")

# Objective Function: Maximize Profit (Revenue - Costs)
# First, calculate revenue
revenue = quicksum(
    flight_vars[i, j, k] *
    (5.9 * (distance_data.loc[i, j] ** -0.76) + 0.043) * distance_data.loc[i, j] *
    aircraft_data.loc[k, 'Seats'] * LOAD_FACTOR
    for i in demand_data.index
    for j in demand_data.columns
    if i != j
    for k in aircraft_data.index
)

# Now, calculate costs
# Lease costs
lease_costs = quicksum(
    aircraft_vars[k] * aircraft_data.loc[k, 'Lease_Cost']
    for k in aircraft_data.index
)

# Operating costs
operating_costs = quicksum(
    flight_vars[i, j, k] * (
        aircraft_data.loc[k, 'Fixed_Cost'] +
        (aircraft_data.loc[k, 'Time_Cost'] * (distance_data.loc[i, j] / aircraft_data.loc[k, 'Speed'])) +
        (aircraft_data.loc[k, 'Fuel_Cost'] * (FUEL_COST ** 1.5) * distance_data.loc[i, j])
    ) * (ECONOMIES_OF_SCALE if (i == HUB_AIRPORT or j == HUB_AIRPORT) else 1)
    for i in demand_data.index
    for j in demand_data.columns
    if i != j
    for k in aircraft_data.index
)

# Total costs
total_costs = lease_costs + operating_costs

# Set objective to maximize profit
model.setObjective(revenue - total_costs, GRB.MAXIMIZE)

# Constraints
# Demand constraints: The total capacity offered must be at least equal to the demand
for i in demand_data.index:
    for j in demand_data.columns:
        if i != j and demand_data.loc[i, j] > 0:
            total_capacity = quicksum(
                flight_vars[i, j, k] * aircraft_data.loc[k, 'Seats'] * LOAD_FACTOR
                for k in aircraft_data.index
            )
            model.addConstr(
                total_capacity >= demand_data.loc[i, j],
                name=f"Demand_{i}_{j}"
            )

# Aircraft utilization constraints
for k in aircraft_data.index:
    total_flight_hours = quicksum(
        flight_vars[i, j, k] * (
            (distance_data.loc[i, j] / aircraft_data.loc[k, 'Speed']) +
            (aircraft_data.loc[k, 'TAT'] / 60)  # Convert TAT to hours
        )
        for i in demand_data.index
        for j in demand_data.columns
        if i != j
    )
    model.addConstr(
        total_flight_hours <= aircraft_vars[k] * MAX_HOURS_PER_WEEK,
        name=f"Utilization_{k}"
    )

# Range constraints
for i in demand_data.index:
    for j in demand_data.columns:
        if i != j and distance_data.loc[i, j] > 0:
            for k in aircraft_data.index:
                model.addConstr(
                    flight_vars[i, j, k] * distance_data.loc[i, j] <=
                    flight_vars[i, j, k] * aircraft_data.loc[k, 'Max_Range'],
                    name=f"Range_{i}_{j}_{k}"
                )

# Runway constraints
# Assuming we have runway length data per airport (not provided in the assignment)
# You would check if the required runway length is available at both airports
# For simplicity, we'll skip this unless data is available

# Solve the model
model.optimize()

# Print the results
if model.status == GRB.OPTIMAL:
    print(f"Optimal Profit: €{model.objVal:,.2f}")
    print("\nAircraft to Lease:")
    for k in aircraft_data.index:
        num_ac = aircraft_vars[k].X
        if num_ac > 0:
            print(f" - {k}: {int(num_ac)} aircraft")
    print("\nFlight Schedule:")
    for i in demand_data.index:
        for j in demand_data.columns:
            if i != j:
                for k in aircraft_data.index:
                    freq = flight_vars[i, j, k].X
                    if freq > 0:
                        print(f" - From {i} to {j} with {k}: {int(freq)} flights per week")
else:
    print("No optimal solution found.")
