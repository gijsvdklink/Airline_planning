from gurobipy import *
from utils.distance_calculations import calculate_distance
# Data
Distance  = calculate_distance(lat1, lon1, lat2, lon2)
Airports = ['C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'I4', 'J4', 'K4', 'L4', 'M4', 'N4', 'O4', 'P4', 'Q4', 'R4', 'S4', 'T4', 'U4', 'V4']
airports = range(len(Airports))
CASK = 0.12
LF = 0.75
s = 120
sp = 870
LTO = 20/60
BT = 10 * 7
AC = 2
# yield #yield_matrix = [[5.9 * (distance[i][j] ** -0.76) + 0.043
 # Path to the spreadsheet file
file_path = 'data/DemandGroup16.xlsx'

# Load the workbook and select the active sheet
wb = openpyxl.load_workbook(file_path)
sheet = wb.active  # Use `wb['SheetName']` if you want a specific sheet

# Define the range of cells containing the matrix
start_row, start_col = 13, 3  # C13 (row 13, column 3)
end_row, end_col = 32, 22    # V32 (row 32, column 22)

# Extract the matrix into a 2D Python list
matrix = []
for row in sheet.iter_rows(min_row=start_row, max_row=end_row, min_col=start_col, max_col=end_col, values_only=True):
    matrix.append(list(row))

# Print the extracted matrix
for row in matrix:
    print(row)
y = matrix[]
q = Forecast demand file
distance =  Distance
# Start modelling optimization problem
m = Model('practice')
x = {}
z = {}
for i in airports:
    for j in airports:
        x[i,j] = m.addVar(obj = y*distance[i][j],lb=0, vtype=GRB.INTEGER)
        z[i,j] = m.addVar(obj = -CASK*distance[i][j]*s, lb=0,vtype=GRB.INTEGER)

m.update()
profit = quicksum(y * distance[i][j] * x[i, j] for i in airports for j in airports) - \
         quicksum(CASK * distance[i][j] * s * z[i, j] for i in airports for j in airports)
m.setObjective(m.getObjective(profit), GRB.MAXIMIZE)  # The objective is to maximize profit

for i in airports:
    for j in airports:
        m.addConstr(x[i,j] <= q[i][j]) #C1
        m.addConstr(x[i, j] <=z[i,j]*s*LF) #C2
    m.addConstr(quicksum(z[i,j] for j in airports), GRB.EQUAL, quicksum(z[j, i] for j in airports)) #C3

m.addConstr(quicksum(quicksum((distance[i][j]/sp+LTO)*z[i,j] for i in airports) for j in airports) <= BT*AC) #C4


m.update()
# m.write('test.lp')
# Set time constraint for optimization (5minutes)
# m.setParam('TimeLimit', 1 * 60)
# m.setParam('MIPgap', 0.009)
m.optimize()
# m.write("testout.sol")
status = m.status

if status == GRB.Status.UNBOUNDED:
    print('The model cannot be solved because it is unbounded')

elif status == GRB.Status.OPTIMAL or True:
    f_objective = m.objVal
    print('***** RESULTS ******')
    print('\nObjective Function Value: \t %g' % f_objective)

elif status != GRB.Status.INF_OR_UNBD and status != GRB.Status.INFEASIBLE:
    print('Optimization was stopped with status %d' % status)


# Print out Solutions
print()
print("Frequencies:----------------------------------")
print()
for i in airports:
    for j in airports:
        if z[i,j].X >0:
            print(Airports[i], ' to ', Airports[j], z[i,j].X)