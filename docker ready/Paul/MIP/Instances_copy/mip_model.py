from ortools.linear_solver import pywraplp
import numpy as np
import os 
import json
import time
import subprocess

def check_solutions_with_external_script(input_folder, results_folder):
    """
    Calls the external solution checker script using subprocess to check all generated solutions.
    """
    try:
        # Call the solution checker, passing the input folder and results folder
        subprocess.run(["python", "solution_checker.py", input_folder, results_folder], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Solution checker failed with error: {str(e)}")

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
    
    # Print the parsed input variables
    #print("Number of couriers (m):", m)
    #print("Number of items (n):", n)
    #print("Courier capacities:", capacities)
    #print("Item sizes:", sizes)
    #print("Distance matrix:")
    #for row in distance_matrix:
    #    print(row)
    
    return m, n, capacities, sizes, np.array(distance_matrix)

def solve_mcp(file_path, timeout = 299):
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

    lower_bound = max(
        max(D[n, j] + D[j, n] for j in range(num_nodes - 1)),  # Depot to farthest point and back
        max(D[i, j] for i in range(num_nodes - 1) for j in range(num_nodes - 1) if i != j)  # Max distance between customers
    )
    upper_bound = sum(
        max(D[i, j] for j in range(num_nodes)) for i in range(num_nodes)
    ) + max(D[n, j] + D[j, n] for j in range(num_nodes - 1))  # All customers served independently

    # Set bounds on the objective variable
    solver.Add(z >= lower_bound)
    solver.Add(z <= upper_bound)

    # Set a time limit of 300 seconds (5 minutes)
    solver.SetTimeLimit(timeout * 1000)  # Time limit is in milliseconds

    # Objective: Minimize the maximum distance traveled by any courier
    solver.Minimize(z)

    # Constraints
    # 1. Each customer must be visited exactly once
    for j in range(num_nodes - 1):  # Customer nodes 0 to n-1
        solver.Add(
            sum(x[i, j, k] for i in range(num_nodes) if i != j for k in range(m)) == 1
        )
    
    # 2. Flow conservation constraints for customers
    # For every customer node, the sum of incoming flows equals the sum of outgoing flows
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

    # Solve the problem
    start_time = time.time()
    status = solver.Solve()
    end_time = time.time()
    runtime = end_time - start_time

    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        # Extract solution
        max_dist = solver.Objective().Value()
        solution = []
        for k in range(m):
            route = []
            for i in range(num_nodes):
                for j in range(num_nodes):
                    if x[i, j, k].solution_value() > 0.5:
                        route.append((i, j))
            solution.append(route)
        #print(solution)

        return {
            "time": int(runtime) if runtime < timeout else timeout,
            "optimal": status == pywraplp.Solver.OPTIMAL,
            "obj": max_dist,
            "sol": solution
        }
    else:
        return {
            "time": timeout,
            "optimal": False,
            "obj": None,
            "sol": "NO SOLUTION FOUND"
        }

def run_batch_instances(instance_dir, output_dir, timeout=300):
    """Runs the solver on all instances in a directory and saves results in JSON format."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    instance_files = sorted([f for f in os.listdir(instance_dir) if f.endswith('.dat')])

    for instance_file in instance_files:
        instance_path = os.path.join(instance_dir, instance_file)
        print(f"Processing {instance_path}...")

        try:
            result = solve_mcp(instance_path)

            # Create a subdirectory for the instance
            instance_name = os.path.splitext(instance_file)[0]
            instance_output_dir = os.path.join(output_dir, instance_name)
            os.makedirs(instance_output_dir, exist_ok=True)

            # Save result to JSON file
            output_file = os.path.join(instance_output_dir, f"{instance_name}.json")
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=4)

            print(f"Result saved to {output_file}")
        except Exception as e:
            print(f"Error processing {instance_path}: {e}")

if __name__ == "__main__":
    # Define instance directory and output directory
    instance_dir = "Instances_copy"  # Directory containing .dat files
    output_dir = "res/MIP/"      # Directory to store JSON results
    dat_files_dir = '../Instances'
    # Run the solver for all instances
    #run_batch_instances(instance_dir, output_dir, timeout=299)

    check_solutions_with_external_script(dat_files_dir, output_dir)