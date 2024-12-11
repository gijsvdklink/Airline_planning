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
    'BT': [70, 70, 70, 70], 
    'Speed': [550, 820, 850, 870],  # in km/h

    'LF': [0.75, 0.75, 0.75, 0.75],  # Load Factor
}, columns=['Type', 'Seats', 'Max_Range', 'Lease_Cost', 'CASK', 'Fixed_Cost', 'Time_Cost', 'Fuel_Cost', 'TAT', 'Speed', 'BT', 'LF'])

print (demand_data)
print(distance_data)
# Parameters
HOURS_PER_DAY = 10
DAYS_PER_WEEK = 7
MAX_HOURS_PER_WEEK = HOURS_PER_DAY * DAYS_PER_WEEK
HUB = 'EDDF'  # Frankfurt

# Set aircraft type as index for easy access
aircraft_data.set_index('Type', inplace=True)
print(aircraft_data)
# Create the optimization model
model = Model("Fleet_and_Network_Development")

# Decision Variables
# Direct passenger flow: xij (from i to j)
direct_flow = model.addVars(demand_data.index, demand_data.columns, vtype=GRB.INTEGER, name="DirectFlow")
print ('the direct flow =', demand_data.index, demand_data.columns)
# Transferred passenger flow via hub: wij (from i to j via hub)
transferred_flow = model.addVars(demand_data.index, demand_data.columns, vtype=GRB.INTEGER, name="TransferredFlow")

# Flight frequency: zijk (number of flights from i to j with aircraft k)
flight_freq = model.addVars(demand_data.index, demand_data.columns, aircraft_data.index, vtype=GRB.INTEGER, name="FlightFreq")

# Number of aircraft leased: ACk (number of aircraft of type k)
aircraft_vars = model.addVars(aircraft_data.index, vtype=GRB.INTEGER, name="NumAircraft")

# Objective Function: Maximize Profit
# Revenue from direct and transferred flows
revenue = quicksum(
    direct_flow[i, j] * (5.9 * (distance_data.loc[i, j] ** -0.76) + 0.043) * distance_data.loc[i, j]
    for i in demand_data.index for j in demand_data.columns if i != j
) + quicksum(
    transferred_flow[i, j] * (5.9 * (distance_data.loc[i, j] ** -0.76) + 0.043) * distance_data.loc[i, j]
    for i in demand_data.index for j in demand_data.columns if i != j
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

# Set Objective: Maximize (Revenue - Costs)
model.setObjective(revenue - total_costs, GRB.MAXIMIZE)

# Constraints

# C1: Demand Satisfaction
for i in demand_data.index:
    for j in demand_data.columns:
        if i != j:
            model.addConstr(
                direct_flow[i, j] + transferred_flow[i, j] <= demand_data.loc[i, j],
                name=f"Demand_Satisfaction_{i}_{j}"
            )

# C2: Restrict Flight Frequencies to Hub Routes Only
# Disallow flights between non-hub airports and eliminate passenger flows between them
for i in demand_data.index:
    for j in demand_data.columns:
        if i != j and i != HUB and j != HUB:
            # Disallow flight frequencies between non-hub airports
            for k in aircraft_data.index:
                model.addConstr(
                    flight_freq[i, j, k] == 0,
                    name=f"Disallow_NonHub_Flight_{i}_{j}_{k}"
                )
            # Eliminate passenger flows between non-hub airports
            model.addConstr(
                direct_flow[i, j] == 0,
                name=f"Zero_DirectFlow_{i}_{j}"
            )
            model.addConstr(
                transferred_flow[i, j] == 0,
                name=f"Zero_TransferredFlow_{i}_{j}"
            )

# C3: Aircraft Flow Conservation
for k in aircraft_data.index:
    for i in demand_data.index:
        if i == HUB:
            # For hub airport, flights departing should equal flights arriving
            model.addConstr(
                quicksum(flight_freq[i, j, k] for j in demand_data.columns if j != i) ==
                quicksum(flight_freq[j, i, k] for j in demand_data.index if j != i),
                name=f"Flow_Conservation_Hub_{i}_{k}"
            )
        else:
            # For non-hub airports, departures to hub must equal arrivals from hub
            model.addConstr(
                quicksum(flight_freq[i, j, k] for j in demand_data.columns if j == HUB) ==
                quicksum(flight_freq[j, i, k] for j in demand_data.index if j == HUB),
                name=f"Flow_Conservation_NonHub_{i}_{k}"
            )

# C4: Flight Time and Range Constraints
for k in aircraft_data.index:
    # Total flight time for aircraft type k should not exceed Block Time * Number of Aircraft
    total_flight_time = quicksum(
        (distance_data.loc[i, j] / aircraft_data.loc[k, 'Speed'] + 
         (1.5 * aircraft_data.loc[k, 'TAT'] / 60)) * flight_freq[i, j, k]
        for i in demand_data.index for j in demand_data.columns if i != j
    )
    model.addConstr(
        total_flight_time <= aircraft_data.loc[k, 'BT'] * aircraft_vars[k],
        name=f"Flight_Time_Limit_{k}"
    )
    
    # Range Constraint: Only allow flights within the aircraft's range
    for i in demand_data.index:
        for j in demand_data.columns:
            if i != j:
                if distance_data.loc[i, j] > aircraft_data.loc[k, 'Max_Range']:
                    model.addConstr(
                        flight_freq[i, j, k] == 0,
                        name=f"Range_Limit_{i}_{j}_{k}"
                    )

# C5: Link Passenger Flows to Flight Frequencies Without Big-M
# Ensure that passenger flows are carried by scheduled flights
for i in demand_data.index:
    for j in demand_data.columns:
        if i != j and (i == HUB or j == HUB):
            # Direct Flows
            model.addConstr(
                direct_flow[i, j] <= quicksum(flight_freq[i, j, k] * aircraft_data.loc[k, 'Seats'] * aircraft_data.loc[k, 'LF'] for k in aircraft_data.index),
                name=f"DirectFlow_Link_{i}_{j}"
            )
            # Transferred Flows
            model.addConstr(
                transferred_flow[i, j] <= quicksum(flight_freq[i, j, k] * aircraft_data.loc[k, 'Seats'] * aircraft_data.loc[k, 'LF'] for k in aircraft_data.index),
                name=f"TransferredFlow_Link_{i}_{j}"
            )
            # Additional Constraints to Link Flight Frequencies to Passenger Flows
            # Ensure that flights are scheduled to carry passenger flows
            model.addConstr(
                quicksum(flight_freq[i, j, k] for k in aircraft_data.index) >= 
                (direct_flow[i, j] + transferred_flow[i, j]) / max(aircraft_data.loc[k, 'Seats'] * aircraft_data.loc[k, 'LF'] for k in aircraft_data.index),
                name=f"Min_FlightFreq_Link_{i}_{j}"
            )

# Optional: Set Gurobi parameters for better output
model.setParam('OutputFlag', 1)  # Enable Gurobi's output
model.setParam('LogFile', 'gurobi_log.txt')  # Save logs to a file

# Solve the model
model.optimize()

# Function to safely retrieve variable values
def get_var_value(var):
    if var.X is not None:
        return var.X
    else:
        return 0

# Print the results
if model.status == GRB.OPTIMAL:
    print(f"Optimal Profit: €{model.objVal:,.2f}")
    
    print("\nAircraft to Lease:")
    any_aircraft_leased = False
    for k in aircraft_data.index:
        num_ac = get_var_value(aircraft_vars[k])
        if num_ac > 0:
            any_aircraft_leased = True
            print(f" - {k}: {int(num_ac)} aircraft")
    if not any_aircraft_leased:
        print(" - No aircraft leased.")
    
    print("\nFlight Schedule:")
    any_flights_scheduled = False
    for i in demand_data.index:
        for j in demand_data.columns:
            if i != j and (i == HUB or j == HUB):
                for k in aircraft_data.index:
                    freq = get_var_value(flight_freq[i, j, k])
                    if freq > 0:
                        any_flights_scheduled = True
                        print(f" - From {i} to {j} with {k}: {int(freq)} flights per week")
    if not any_flights_scheduled:
        print(" - No flights scheduled.")
    
    print("\nPassenger Flows:")
    print("Direct Flows:")
    any_direct_flows = False
    for i in demand_data.index:
        for j in demand_data.columns:
            if i != j and (i == HUB or j == HUB):
                flow = get_var_value(direct_flow[i,j])
                if flow > 0:
                    any_direct_flows = True
                    print(f" - DirectFlow from {i} to {j}: {flow} passengers")
    if not any_direct_flows:
        print(" - No direct passenger flows.")
    
    print("Transferred Flows:")
    any_transferred_flows = False
    for i in demand_data.index:
        for j in demand_data.columns:
            if i != j and (i == HUB or j == HUB):
                flow = get_var_value(transferred_flow[i,j])
                if flow > 0:
                    any_transferred_flows = True
                    print(f" - TransferredFlow from {i} to {j}: {flow} passengers")
    if not any_transferred_flows:
        print(" - No transferred passenger flows.")
    
    print("\nAirport Activation:")
    # In this revised model, all flights involve the hub, so the hub is always active
    print(f" - Hub Airport {HUB} is active.")
    # List other airports that have flights
    active_airports = set()
    for i in demand_data.index:
        for j in demand_data.columns:
            if i != j and (i == HUB or j == HUB):
                for k in aircraft_data.index:
                    if get_var_value(flight_freq[i, j, k]) > 0:
                        active_airports.add(i)
                        active_airports.add(j)
    # Remove hub from active airports as it's already listed
    active_airports.discard(HUB)
    for airport in active_airports:
        print(f" - Airport {airport} is active.")
else:
    print("No optimal solution found.")
