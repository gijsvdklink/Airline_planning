from gurobipy import Model, GRB, quicksum
import pandas as pd
import numpy as np

# Constants
LOAD_FACTOR = 0.75
HUB_ECONOMIES = 0.7
HOURS_PER_DAY = 10
DAYS_PER_WEEK = 7
BLOCK_TIME = HOURS_PER_DAY * DAYS_PER_WEEK  # Weekly available block time
FUEL_COST = 1.42  # EUR/gallon

# Aircraft data
aircraft_data = {
    "Aircraft 1": {"speed": 550, "seats": 45, "lease": 15000, "CX": 300, "CT": 750, "CF": 1.0, "range": 1500},
    "Aircraft 2": {"speed": 820, "seats": 70, "lease": 34000, "CX": 600, "CT": 775, "CF": 2.0, "range": 3300},
    "Aircraft 3": {"speed": 850, "seats": 150, "lease": 80000, "CX": 1250, "CT": 1400, "CF": 3.75, "range": 6300},
    "Aircraft 4": {"speed": 870, "seats": 320, "lease": 190000, "CX": 2000, "CT": 2800, "CF": 9.0, "range": 12000},
}

# File paths
distance_file = "distance_matrix_with_city_names.csv"
demand_file = "Future_Demand_2025_with_Gravity_Model.xlsx"

# Load data
distance_df = pd.read_csv(distance_file, index_col=0)
demand_df = pd.read_excel(demand_file, index_col=0)

# Debug: Check if input data is valid
print("\nDistance Matrix:\n", distance_df)
print("\nDemand Matrix:\n", demand_df)

# Yield calculation
def calculate_yield(distance):
    if distance == 0:
        return 0  # Handle zero distances
    return 5.9 * distance ** -0.76 + 0.043

# Calculate yields
yields = distance_df.applymap(calculate_yield)

# Create the Gurobi model
model = Model("Network_and_Fleet_Development")

# Variables
x = {}  # Passenger flow
z = {}  # Flight frequency
ac_lease = {}  # Number of leased aircraft per type

for origin in demand_df.index:
    for destination in demand_df.columns:
        if origin != destination:
            x[origin, destination] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"x_{origin}_{destination}")
            z[origin, destination] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"z_{origin}_{destination}")

for aircraft_type in aircraft_data.keys():
    ac_lease[aircraft_type] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"ac_lease_{aircraft_type}")

model.update()

# Objective function: Maximize profit
model.setObjective(
    quicksum(
        yields.loc[o, d] * distance_df.loc[o, d] * x[o, d]
        - quicksum(
            (
                aircraft_data[a]["CX"]
                + (aircraft_data[a]["CT"] * distance_df.loc[o, d] / aircraft_data[a]["speed"])
                + (aircraft_data[a]["CF"] * FUEL_COST ** 1.5 * distance_df.loc[o, d])
            )
            * z[o, d]
            for a in aircraft_data.keys()
        )
        - quicksum(aircraft_data[a]["lease"] * ac_lease[a] for a in aircraft_data.keys())
        for o in demand_df.index
        for d in demand_df.columns
        if o != d
    ),
    GRB.MAXIMIZE,
)

# Constraints
for origin in demand_df.index:
    for destination in demand_df.columns:
        if origin != destination:
            # Demand constraint
            model.addConstr(
                x[origin, destination] <= demand_df.loc[origin, destination] * LOAD_FACTOR, f"demand_{origin}_{destination}"
            )
            # Capacity constraint
            model.addConstr(
                x[origin, destination] <= quicksum(
                    aircraft_data[a]["seats"] * z[origin, destination] for a in aircraft_data.keys()
                ),
                f"capacity_{origin}_{destination}",
            )

# Aircraft productivity constraint
for aircraft_type, data in aircraft_data.items():
    model.addConstr(
        quicksum(
            (distance_df.loc[o, d] / data["speed"] + data["CX"] / 60) * z[o, d]
            for o in demand_df.index
            for d in demand_df.columns
            if o != d
        )
        <= BLOCK_TIME * ac_lease[aircraft_type],
        f"productivity_{aircraft_type}",
    )

model.update()

# Solve the model
model.optimize()

# Debug: Display variable values
if model.status == GRB.OPTIMAL:
    print("\nOptimal Solution Found:")
    print("Profit:", model.objVal)
    print("\nFlight Frequencies:")
    for o, d in z.keys():
        if z[o, d].x > 0:
            print(f"Route {o} -> {d}: {z[o, d].x} flights")
    print("\nLeased Aircraft:")
    for a in ac_lease.keys():
        if ac_lease[a].x > 0:
            print(f"{a}: {ac_lease[a].x} aircraft")
else:
    print("No optimal solution found.")
