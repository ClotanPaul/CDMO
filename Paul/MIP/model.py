import pulp

def read_dat_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    m = int(lines[0].strip())  # Number of couriers
    n = int(lines[1].strip())  # Number of items

    capacities = list(map(int, lines[2].split()))
    sizes = list(map(int, lines[3].split()))

    # Read the distance matrix
    distances = []
    for line in lines[4:]:
        distances.append(list(map(int, line.split())))

    return m, n, capacities, sizes, distances

# Step 2: Load the data
m, n, l, s, D = read_dat_file('Instances/inst01.dat')

print("Number of couriers (m):", m)
print("Number of items (n):", n)
print("Capacities of couriers:", l)
print("Sizes of items:", s)
print("Distance matrix:")
for row in D:
    print(row)

# Step 3: Define the PuLP model
model = pulp.LpProblem("Multiple_Couriers_Planning", pulp.LpMinimize)

# Decision variables
x = pulp.LpVariable.dicts("x", [(i, j1, j2) for i in range(m) for j1 in range(n+1) for j2 in range(n+1)], cat='Binary')
y = pulp.LpVariable.dicts("y", range(m), lowBound=0)
traveled_max_dist = pulp.LpVariable("traveled_max_dist", lowBound=0)

# Objective: Minimize the maximum distance traveled
model += traveled_max_dist

# Constraints
# Calculate distances
for i in range(m):
    model += y[i] == pulp.lpSum(D[j1][j2] * x[i, j1, j2] for j1 in range(n+1) for j2 in range(n+1))
    model += y[i] <= traveled_max_dist

# Capacity constraints
for i in range(m):
    model += pulp.lpSum(s[j] * pulp.lpSum(x[i, j, j2] for j2 in range(n+1)) for j in range(n)) <= l[i]

# Assignment constraints
for j in range(n):
    model += pulp.lpSum(x[i, j, j2] for i in range(m) for j2 in range(n+1)) == 1

# Start and end at depot
for i in range(m):
    model += pulp.lpSum(x[i, n, j] for j in range(n+1)) == 1
    model += pulp.lpSum(x[i, j, n] for j in range(n+1)) == 1

# Solve the model
model.solve()

# Print results
print(f"Status: {pulp.LpStatus[model.status]}")
print(f"Optimal maximum distance: {pulp.value(traveled_max_dist)}")
for i in range(m):
    print(f"Courier {i+1} route distance: {pulp.value(y[i])}")