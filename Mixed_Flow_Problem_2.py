import pandas as pd
from gurobipy import Model, GRB, quicksum

# Load the spreadsheet
excel_path = "Group_16.xlsx"  # Adjust the file path as necessary
data = pd.ExcelFile(excel_path)

# Extract data from specific sheets
# Assume sheet names and column headers based on the description; adjust as necessary
flights_sheet = data.parse("Flights")  # Replace with actual sheet name for flights
itineraries_sheet = data.parse("Itineraries")  # Replace with actual sheet name for itineraries

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
        delta[(itinerary, flight)] = row.get(f"Assigned to {flight}", 0)

recapture_rate_sheet = data.parse("Recapture")  # Adjust the sheet name if needed
recapture_rate = {}

# Iterate through each row in the Recapture sheet
for _, row in recapture_rate_sheet.iterrows():
    from_itinerary = row["From Itinerary"]  # Use the exact column name
    to_itinerary = row["To Itinerary"]      # Use the exact column name
    rate = row["Recapture Rate"]           # Use the exact column name

    # Store the recapture rate in a dictionary
    recapture_rate[(from_itinerary, to_itinerary)] = rate

# Initialize model
model = Model("RMP")

# Decision variables
x = model.addVars(itineraries, itineraries, lb=0, name="x")

# Objective function
model.setObjective(
    quicksum(fares[r] * x[p, r] for p in itineraries for r in itineraries if p != r),
    GRB.MAXIMIZE
)

# Constraints
# Capacity constraints
for flight in flights:
    model.addConstr(
        quicksum(delta.get((p, flight), 0) * x[p, r] for p in itineraries for r in itineraries if p != r) <= capacity[flight],
        name=f"Capacity_{flight}"
    )

# Demand constraints
for itinerary in itineraries:
    model.addConstr(
        quicksum(x[itinerary, r] / recapture_rate.get((itinerary, r), 1) for r in itineraries if r != itinerary) <= demand[itinerary],
        name=f"Demand_{itinerary}"
    )

# Solve model
model.optimize()

# Display results
if model.status == GRB.OPTIMAL:
    print("Optimal Solution Found!")
    for p in itineraries:
        for r in itineraries:
            if x[p, r].X > 0:
                print(f"Passengers from {p} to {r}: {x[p, r].X}")
else:
    print("No optimal solution found.")
    