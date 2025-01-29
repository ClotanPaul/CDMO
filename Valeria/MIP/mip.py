from ortools.linear_solver import pywraplp
import numpy as np
import os 
import json
import time
import subprocess
import math

def check_solutions_with_external_script(input_folder, results_folder):
    """
    Calls the external solution checker script using subprocess to check all generated solutions.
    """
    try:
        subprocess.run(["python3", "D:/personal/uni/cdo/project/solution_checker.py", input_folder, results_folder], check=True)
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
    
    return m, n, capacities, sizes, np.array(distance_matrix)

def solve_mcp(file_path, solver_type, timeout = 300):
    # Read instance data from the .dat file
    m, n, capacities, sizes, D = read_dat_file(file_path)
    
    num_nodes = n + 1  # Including depot(origin point)

    solver = pywraplp.Solver.CreateSolver(solver_type)

    # Decision variables
    x = {}
    for k in range(m):
        for i in range(num_nodes):
            for j in range(num_nodes):
                x[i, j, k] = solver.BoolVar(f'x_{i}_{j}_{k}')


    lower_bound = math.ceil(max(
        max(D[n, j] + D[j, n] for j in range(num_nodes - 1)),  
        max(D[i, j] for i in range(num_nodes - 1) for j in range(num_nodes - 1) if i != j)  
    ))
    upper_bound = math.ceil(sum(
        max(D[i, j] for j in range(num_nodes)) for i in range(num_nodes)
    ) + max(D[n, j] + D[j, n] for j in range(num_nodes - 1)) )

    y = [solver.IntVar(0, solver.infinity(), f'y_{k}') for k in range(m)]
    z = solver.IntVar(lower_bound, upper_bound, 'z')

    # Set the time limit
    solver.SetTimeLimit(timeout * 1000)

    solver.Minimize(z)

    # Constraints
    # 1. Each distribution point must be visited exactly once
    for j in range(num_nodes - 1):  
        solver.Add(
            sum(x[i, j, k] for i in range(num_nodes) if i != j for k in range(m)) == 1
        )
    
    # 2. Flow conservation constraints for distribution points
    # For every distribution point node, the sum of incoming flows equals the sum of outgoing flows
    for k in range(m):
        for j in range(num_nodes - 1): 
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
        for i in range(num_nodes - 1):  
            for j in range(num_nodes - 1): 
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


    start_time = time.time()
    status = solver.Solve()
    end_time = time.time()
    runtime = end_time - start_time

    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        
        max_dist = solver.Objective().Value()
        solution = []

        for k in range(m):  
            route = []
            current_node = n  
            while True:
                found_next = False
                for j in range(num_nodes):
                    if x[current_node, j, k].solution_value() > 0.5:  # If edge is part of the route
                        if j != n:  
                            route.append(j + 1)
                        current_node = j
                        found_next = True
                        break
                if not found_next or current_node == n:
                    break  # End of the route or returned to depot
            solution.append(route)

        return  {
                "time": int(runtime) if runtime < timeout else int(timeout),
                "optimal": status == pywraplp.Solver.OPTIMAL,
                "obj": round(max_dist),
                "sol": solution  
            }
    return None

def run_batch_instances(instance_dir, output_dir, timeout=300):
    """Runs the solver on all instances in a directory and saves results in JSON format."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    instance_files = sorted([f for f in os.listdir(instance_dir) if f.endswith('.dat')])
    instances_to_include = [13] #list(range(1, 11))+ [13,16] 

    for instance_file in instance_files:
        instance_number = int(''.join(filter(str.isdigit, instance_file)))
        
        # Check if the instance number is in the list of desired instances
        if instance_number not in instances_to_include:
            continue

        instance_path = os.path.join(instance_dir, instance_file)
        print(f"Processing {instance_path}...")

        solvers = ["CBC", "SCIP"]
        try:
            results = {}
            for solver in solvers:
                res = solve_mcp(instance_path, solver)
                if(res != None):
                    results[solver] = solve_mcp(instance_path, solver)

            instance_name = os.path.splitext(instance_file)[0]
            instance_output_dir = os.path.join(output_dir, instance_name)

            os.makedirs(instance_output_dir, exist_ok=True)

            output_file = os.path.join(instance_output_dir, f"{instance_name}.json")
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=4)

            print(f"Result saved to {output_file}")
        except Exception as e:
            print(f"Error processing {instance_path}: {e}")

if __name__ == "__main__":
    instance_dir = "D:\\personal\\uni\\cdo\\project\\Instances"  
    output_dir = "D:\\personal\\uni\\cdo\\project\\res\\MIP\\"      
    dat_files_dir = 'D:\\personal\\uni\\cdo\\project\\Instances'
    run_batch_instances(instance_dir, output_dir, timeout=300)

    #check_solutions_with_external_script(instance_dir, output_dir)