from ortools.linear_solver import pywraplp
import numpy as np
import time

def read_dat_file(file_path):
    """Parse the .dat file to extract instance data."""
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Read the number of couriers and items
    m = int(lines[0].strip())
    n = int(lines[1].strip())

    # Read courier capacities
    capacities = list(map(int, lines[2].strip().split()))

    # Read item sizes
    sizes = list(map(int, lines[3].strip().split()))

    # Read the distance matrix
    distance_matrix = []
    for line in lines[4:]:
        distance_matrix.append(list(map(int, line.strip().split())))

    return m, n, capacities, sizes, np.array(distance_matrix)

def solve_mcp(file_path):
    # Read instance data from the .dat file
    m, n, capacities, sizes, D = read_dat_file(file_path)

    # Adjust indexing: depot is node n, customers are nodes 0 to n-1
    num_nodes = n + 1  # Including depot

    # Create the OR-Tools solver with CBC backend
    solver = pywraplp.Solver.CreateSolver('CBC')
    if not solver:
        print("Solver not found!")
        return

    # Decision variables
    x = {}
    for k in range(m):
        for i in range(num_nodes):
            for j in range(num_nodes):
                x[i, j, k] = solver.BoolVar(f'x_{i}_{j}_{k}')

    y = [solver.IntVar(0, solver.infinity(), f'y_{k}') for k in range(m)]
    z = solver.IntVar(0, solver.infinity(), 'z')

    # Set a time limit of 300 seconds (5 minutes)
    solver.SetTimeLimit(300 * 1000)  # Time limit is in milliseconds

    # Objective: Minimize the maximum distance traveled by any courier
    solver.Minimize(z)

    # Constraints
    # 1. Each customer must be visited exactly once
    for j in range(num_nodes - 1):  # Customer nodes 0 to n-1
        solver.Add(
            sum(x[i, j, k] for i in range(num_nodes) if i != j for k in range(m)) == 1
        )

    # 2. Flow conservation constraints for customers
    for k in range(m):
        for j in range(num_nodes - 1):  # Customer nodes 0 to n-1
            solver.Add(
                sum(x[i, j, k] for i in range(num_nodes) if i != j) ==
                sum(x[j, i, k] for i in range(num_nodes) if i != j)
            )

    # 3. Each courier starts and ends at the depot
    for k in range(m):
        solver.Add(sum(x[n, j, k] for j in range(num_nodes - 1)) == 1)  # Start at depot
        solver.Add(sum(x[j, n, k] for j in range(num_nodes - 1)) == 1)  # End at depot

    # 4. Capacity constraints
    for k in range(m):
        solver.Add(
            sum(
                sizes[j] * x[i, j, k]
                for i in range(num_nodes)
                for j in range(num_nodes - 1)
                if i != j
            ) <= capacities[k]
        )

    # 5. MTZ Subtour elimination constraints
    u = {}
    for k in range(m):
        for j in range(num_nodes):
            u[j, k] = solver.NumVar(0, n, f'u_{j}_{k}')

    # Set u at depot to 0
    for k in range(m):
        solver.Add(u[n, k] == 0)

    # Add MTZ constraints
    for k in range(m):
        for i in range(num_nodes - 1):  # Customer nodes
            for j in range(num_nodes - 1):  # Customer nodes
                if i != j:
                    solver.Add(u[i, k] - u[j, k] + n * x[i, j, k] <= n - 1)

    # 6. Compute the distance traveled by each courier and set y[k]
    for k in range(m):
        total_distance = solver.Sum(
            D[i][j] * x[i, j, k]
            for i in range(num_nodes)
            for j in range(num_nodes)
        )
        solver.Add(y[k] == total_distance)
        solver.Add(z >= y[k])

    # 7. Symmetry-breaking for couriers with equal capacities
    aux_outgoing = {}
    for k in range(m):
        aux_outgoing[k] = solver.IntVar(0, num_nodes - 1, f'aux_outgoing_{k}')

    for k in range(m):
        solver.Add(aux_outgoing[k] <= sum(x[n, j, k] for j in range(num_nodes - 1)))

    equal_capacity_pairs = []
    for k1 in range(m - 1):
        for k2 in range(k1 + 1, m):
            if capacities[k1] == capacities[k2]:
                equal_capacity_pairs.append((k1, k2))

    sym = [solver.BoolVar(f'sym_{k}') for k in range(m)]

    for k1, k2 in equal_capacity_pairs:
        product_sym = solver.BoolVar(f'product_sym_{k1}_{k2}')
        solver.Add(product_sym <= sym[k1])
        solver.Add(product_sym <= sym[k2])
        solver.Add(product_sym >= sym[k1] + sym[k2] - 1)
        solver.Add(
            sum(x[n, j, k1] for j in range(num_nodes - 1)) >=
            sum(x[n, j, k2] for j in range(num_nodes - 1)) - (1 - product_sym) * num_nodes
        )

    # Solve the problem
    start_time = time.time()
    status = solver.Solve()
    end_time = time.time()
    runtime = end_time - start_time

    print("Solver Statistics:")
    print(f"  Number of variables: {solver.NumVariables()}")
    print(f"  Number of constraints: {solver.NumConstraints()}")
    print(f"  Wall time: {solver.WallTime()} ms")
    print(f"  Iterations: {solver.Iterations()}")

    # Check if any solution was found
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        print(f"Solution found with maximum distance: {solver.Objective().Value()}")

        # Print the solution for each courier
        for k in range(m):
            items = set()
            route = []
            for i in range(num_nodes):
                for j in range(num_nodes):
                    if x[i, j, k].solution_value() > 0.5:
                        route.append((i, j))
                        if j != n:
                            items.add(j)  # Items correspond to customer nodes
            print(f"Courier {k + 1}: delivers items {sorted(items)} with distance {y[k].solution_value()}")
            print(f"  Route: {route}")

        # Check if the solution is optimal
        if status == pywraplp.Solver.OPTIMAL:
            print("The solution is optimal.")
        else:
            print("The solution is not optimal, but it is the best found within the time limit.")
    else:
        print("No feasible solution found.")

# Example instance file path
instance_file = '../Instances/inst07.dat'  # Format filenames like inst01.dat
print(f"Processing {instance_file}...")
solve_mcp(instance_file)
print("\n" + "=" * 50 + "\n")
