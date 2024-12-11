import pandas as pd
from gurobipy import Model, GRB, quicksum

# Load the spreadsheet
excel_path = "Group_16.xlsx"  # Adjust the file path as necessary
data = pd.ExcelFile(excel_path)

# Extract data from specific sheets
flights_sheet = data.parse("Flights")
itineraries_sheet = data.parse("Itineraries")
recapture_rate_sheet = data.parse("Recapture")

# Flights data
flights = flights_sheet["Flight No."].tolist()
capacity = dict(zip(flights_sheet["Flight No."], flights_sheet["Capacity"]))

# Itineraries data
itineraries = itineraries_sheet["Itinerary"].tolist()
fares = dict(zip(itineraries_sheet["Itinerary"], itineraries_sheet["Price [EUR]"]))
demand = dict(zip(itineraries_sheet["Itinerary"], itineraries_sheet["Demand"]))

# Assignment matrix
delta = {}
for _, row in itineraries_sheet.iterrows():
    itinerary = row["Itinerary"]
    for flight in flights:
        if row.get(f"Assigned to {flight}", 0) > 0:
            delta[(itinerary, flight)] = row[f"Assigned to {flight}"]

# Recapture rates (filter rates > 0.1)
recapture_rate = {}
for _, row in recapture_rate_sheet.iterrows():
    rate = row["Recapture Rate"]
    if rate > 0.1:
        recapture_rate[(row["From Itinerary"], row["To Itinerary"])] = rate

# Initialize the model
model = Model("RMP")

# Add fictitious itinerary
fictitious_itinerary = "Fictitious"

# Decision variables
x = {}  # Passengers directly assigned from an itinerary to another
for p in itineraries:
    x[(p, fictitious_itinerary)] = model.addVar(lb=0, name=f"x_{p}_fictitious")  # Spilled passengers
    for r in itineraries:
        if p != r and (p, r) in recapture_rate:  # Reallocation variables
            x[(p, r)] = model.addVar(lb=0, name=f"x_{p}_{r}")

# Objective function
model.setObjective(
    quicksum(fares[r] * recapture_rate[(p, r)] * x[(p, r)] for p, r in x if r != fictitious_itinerary),
    GRB.MAXIMIZE
)

# Add capacity constraints
for flight in flights:
    model.addConstr(
        quicksum(delta.get((p, flight), 0) * x[(p, r)] for p, r in x if r != fictitious_itinerary and delta.get((p, flight), 0) > 0) <= capacity[flight],
        name=f"Capacity_{flight}"
    )

# Add demand constraints
for p in itineraries:
    model.addConstr(
        quicksum(x[(p, r)] for r in itineraries if (p, r) in recapture_rate) + x[(p, fictitious_itinerary)] <= demand[p],
        name=f"Demand_{p}"
    )

# Fictitious itinerary constraints
for r in itineraries:
    if r != fictitious_itinerary:
        model.addConstr(
            quicksum(x[(p, r)] for p in itineraries if (p, r) in recapture_rate) <= capacity.get(r, float("inf")),
            name=f"Reallocation_{r}"
        )

# Solve the RMP
model.optimize()

# Display results
if model.status == GRB.OPTIMAL:
    print("Final Optimal Solution Found!")
    for p, r in x:
        if x[(p, r)].X > 0:
            if r == fictitious_itinerary:
                print(f"Passengers spilled from {p} to fictitious itinerary: {x[(p, r)].X}")
            else:
                print(f"Passengers reallocated from {p} to {r}: {x[(p, r)].X}")
else:
    print("No optimal solution found.")