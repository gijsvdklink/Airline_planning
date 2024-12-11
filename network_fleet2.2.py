import pandas as pd
from gurobipy import Model, GRB, quicksum

# Load data
demand_data = pd.read_excel('Future_Demand_2025_with_Gravity_Model.xlsx', index_col=0)
distance_data = pd.read_csv('distance_matrix_with_city_names.csv', index_col=0)

# Aircraft data
aircraft_data = pd.DataFrame({
    'Type': ['Aircraft 1', 'Aircraft 2', 'Aircraft 3', 'Aircraft 4'],
    'Seats': [45, 70, 150, 320],
    'Max_Range': [1500, 3300, 6300, 12000],
    'Lease_Cost': [15000, 34000, 80000, 190000],
    'CASK': [0.05, 0.04, 0.03, 0.02],  # Example CASK values (€/seat-km)
    'Fixed_Cost': [300, 600, 1250, 2000],
    'Time_Cost': [750, 775, 1400, 2800],
    'Fuel_Cost': [1.0, 2.0, 3.75, 9.0],
    'TAT': [25, 35, 45, 60],  # Turn-Around Time in minutes
    'Speed': [550, 820, 850, 870],  # in km/h
    'LF': [0.75, 0.75, 0.75, 0.75],  # Load Factor
}, columns=['Type', 'Seats', 'Max_Range', 'Lease_Cost', 'CASK', 'Fixed_Cost', 'Time_Cost', 'Fuel_Cost', 'TAT', 'Speed', 'LF'])

# Parameters
HOURS_PER_DAY = 10
HUB = 'EDDF'  # Frankfurt

# Set aircraft type as index for easy access
aircraft_data.set_index('Type', inplace=True)

# Create the optimization model
model = Model("Daily_Fleet_and_Network_Development")

# Decision Variables
# Daily passenger flow (direct and transferred)
direct_flow = model.addVars(demand_data.index, demand_data.columns, vtype=GRB.INTEGER, name="DirectFlow")
transferred_flow = model.addVars(demand_data.index, demand_data.columns, vtype=GRB.INTEGER, name="TransferredFlow")

# Daily flight frequency
flight_freq = model.addVars(demand_data.index, demand_data.columns, aircraft_data.index, vtype=GRB.INTEGER, name="FlightFreq")

# Number of aircraft leased
aircraft_vars = model.addVars(aircraft_data.index, vtype=GRB.INTEGER, name="NumAircraft")

# Objective Function: Maximize Profit
# Revenue from direct and transferred flows
revenue = quicksum(
    direct_flow[i, j] * (5.9 * (distance_data.loc[i, j] ** -0.76) + 0.043) * distance_data.loc[i, j]
    for i in demand_data.index for j in demand_data.columns if i != j
) + quicksum(
    transferred_flow[i, j] * (
        (5.9 * (distance_data.loc[i, HUB] ** -0.76) + 0.043) * distance_data.loc[i, HUB] +
        (5.9 * (distance_data.loc[HUB, j] ** -0.76) + 0.043) * distance_data.loc[HUB, j]
    )
    for i in demand_data.index for j in demand_data.columns if i != j and i != HUB and j != HUB
)

# Costs: CASK-based operational costs and Lease Costs
operational_costs = quicksum(
    flight_freq[i, j, k] * aircraft_data.loc[k, 'CASK'] * distance_data.loc[i, j] * aircraft_data.loc[k, 'Seats'] * aircraft_data.loc[k, 'LF']
    for i in demand_data.index for j in demand_data.columns if i != j for k in aircraft_data.index
)

lease_costs = quicksum(
    aircraft_vars[k] * aircraft_data.loc[k, 'Lease_Cost']
    for k in aircraft_data.index
)

total_costs = operational_costs + lease_costs
model.setObjective(revenue - total_costs, GRB.MAXIMIZE)

# Constraints

# C1: Daily Demand Satisfaction
for i in demand_data.index:
    for j in demand_data.columns:
        if i != j:
            model.addConstr(
                direct_flow[i, j] + transferred_flow[i, j] <= demand_data.loc[i, j] / 7,  # Weekly demand divided by 7
                name=f"Demand_Satisfaction_{i}_{j}"
            )

# C2: Restrict Flight Frequencies to Hub Routes Only
for i in demand_data.index:
    for j in demand_data.columns:
        if i != j and i != HUB and j != HUB:
            for k in aircraft_data.index:
                model.addConstr(
                    flight_freq[i, j, k] == 0,
                    name=f"Disallow_NonHub_Flight_{i}_{j}_{k}"
                )

# C3: Aircraft Flow Conservation
for k in aircraft_data.index:
    for airport in demand_data.index:
        model.addConstr(
            quicksum(flight_freq[i, airport, k] for i in demand_data.index if i != airport) ==
            quicksum(flight_freq[airport, j, k] for j in demand_data.columns if j != airport),
            name=f"Aircraft_Flow_Conservation_{airport}_{k}"
        )

# C4: Flight Time and TAT Constraints
for k in aircraft_data.index:
    total_flight_time = quicksum(
        (distance_data.loc[i, j] / aircraft_data.loc[k, 'Speed'] +
         (1.5 * aircraft_data.loc[k, 'TAT'] / 60 if j == HUB or i == HUB else aircraft_data.loc[k, 'TAT'] / 60)) * flight_freq[i, j, k]
        for i in demand_data.index for j in demand_data.columns if i != j
    )
    model.addConstr(
        total_flight_time <= HOURS_PER_DAY * aircraft_vars[k],  # 10 hours per day
        name=f"Flight_Time_Limit_{k}"
    )

# C5: Link Passenger Flows to Flight Frequencies
for i in demand_data.index:
    for j in demand_data.columns:
        if i != j and (i == HUB or j == HUB):
            model.addConstr(
                direct_flow[i, j] <= quicksum(flight_freq[i, j, k] * aircraft_data.loc[k, 'Seats'] * aircraft_data.loc[k, 'LF'] for k in aircraft_data.index),
                name=f"DirectFlow_Link_{i}_{j}"
            )
        if i != j and i != HUB and j != HUB:
            model.addConstr(
                transferred_flow[i, j] <= quicksum(flight_freq[i, HUB, k] * aircraft_data.loc[k, 'Seats'] * aircraft_data.loc[k, 'LF'] for k in aircraft_data.index),
                name=f"TransferredFlow_FirstLeg_{i}_{j}"
            )
            model.addConstr(
                transferred_flow[i, j] <= quicksum(flight_freq[HUB, j, k] * aircraft_data.loc[k, 'Seats'] * aircraft_data.loc[k, 'LF'] for k in aircraft_data.index),
                name=f"TransferredFlow_SecondLeg_{i}_{j}"
            )

# Solve the model
model.optimize()

# Output results
if model.status == GRB.OPTIMAL:
    print(f"Optimal Profit: €{model.objVal:,.2f}")
    print("\nAircraft to Lease:")
    for k in aircraft_data.index:
        print(f" - {k}: {int(model.getVarByName(f'NumAircraft[{k}]').x)} aircraft")
    print("\nFlight Schedule:")
    for i in demand_data.index:
        for j in demand_data.columns:
            for k in aircraft_data.index:
                freq = model.getVarByName(f'FlightFreq[{i},{j},{k}]').x
                if freq > 0:
                    print(f" - From {i} to {j} with {k}: {freq:.0f} flights per day")
else:
    print("No optimal solution found.")
