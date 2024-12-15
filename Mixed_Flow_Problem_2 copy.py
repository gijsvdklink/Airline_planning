import pandas as pd
from gurobipy import Model, GRB, quicksum

# Load the spreadsheet
excel_path = "data/Group_16.xlsx"  # Adjust the file path as necessary
data = pd.ExcelFile(excel_path)

# Extract data from specific sheets
flights_sheet = data.parse("Flights")  # Replace with actual sheet name for flights
itineraries_sheet = data.parse("Itineraries")  # Replace with actual sheet name for itineraries
recapture_rate_sheet = data.parse("Recapture")  # Adjust the sheet name if needed

# Flights data
flights = flights_sheet["Flight No."].tolist()
capacity = dict(zip(flights_sheet["Flight No."], flights_sheet["Capacity"]))

L = flights  # Set of flights

# Itineraries data
itineraries = itineraries_sheet["Itinerary"].tolist()
fares = dict(zip(itineraries_sheet["Itinerary"], itineraries_sheet["Price [EUR]"]))
demand = dict(zip(itineraries_sheet["Itinerary"], itineraries_sheet["Demand"]))

P = itineraries  # Set of itineraries

# Assignment matrix
delta = {}
for _, row in itineraries_sheet.iterrows():
    itinerary = row["Itinerary"]
    for flight in flights:
        delta[(itinerary, flight)] = row.get(f"Assigned to {flight}", 0)

# Recapture rates
recapture_rate = {}
for _, row in recapture_rate_sheet.iterrows():
    from_itinerary = row["From Itinerary"]  # Use the exact column name
    to_itinerary = row["To Itinerary"]      # Use the exact column name
    rate = row["Recapture Rate"]           # Use the exact column name
    recapture_rate[(from_itinerary, to_itinerary)] = rate

# Initialize model
model = Model("RMP")

# Decision variables
x = model.addVars(P, P, lb=0, name="x")  # Passengers reallocated
t = model.addVars(P, P, lb=0, name="t")  # Temporary decision variable for reallocation

# Objective function
model.setObjective(
    quicksum(
        (fares[p] - recapture_rate.get((p, r), 0) * fares.get(r, 0)) * t[p, r]
        for p in P for r in P
    ),
    GRB.MINIMIZE
)

# Constraints

# Capacity constraint (C1)
for i in L:
    model.addConstr(
        quicksum(delta[p, i] * x[p, r] for p in P for r in P) <= capacity[i],
        name=f"Capacity_Constraint_{i}"
    )

# Demand constraint (C2)
for p in P:
    model.addConstr(
        quicksum(x[p, r] / recapture_rate.get((p, r), 1) for r in P if recapture_rate.get((p, r), 0) > 0) <= demand[p],
        name=f"Demand_Constraint_{p}"
    )

# Non-negativity constraint (C3)
for p in P:
    for r in P:
        model.addConstr(
            x[p, r] >= 0,
            name=f"NonNegativity_{p}_{r}"
        )

# Flight allocation constraint
for i in L:
    model.addConstr(
        quicksum(delta[p, i] * t[p, r] for p in P for r in P) -
        quicksum(delta[p, i] * recapture_rate.get((p, r), 0) * t[p, r] for p in P for r in P) >=
        demand.get(i, 0) - capacity.get(i, 0),
        name=f"Flight_Allocation_{i}"
    )

# Solve model
model.optimize()

# Display results
if model.status == GRB.OPTIMAL:
    print("Optimal Solution Found!")
    for p in P:
        for r in P:
            if x[p, r].X > 0:
                print(f"Passengers from {p} to {r}: {x[p, r].X}")
else:
    print("No optimal solution found.")



# Fictious itinerary serves as solution for dual variables
#pricing  