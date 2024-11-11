import os
import time
import minizinc
import json
from datetime import timedelta
import subprocess

def traverse_lists(lists):
    solution = []
    for lst in lists:
        n = len(lst)
        current_index = n
        visited = []

        if not lst:
            solution.append([])
            continue

        if lst == list(range(1, len(lst) + 1)):
            solution.append([])
            continue

        while lst[current_index - 1] != n:
            if current_index != n:
                visited.append(current_index)
            current_index = lst[current_index - 1]
        
        visited.append(current_index)
        solution.append(visited)
    return solution

def run_minizinc_with_restarts(dzn_files_dir, model_file, output_dir, restart_values, timeout=300):
    model = minizinc.Model(model_file)
    solver = minizinc.Solver.lookup("gecode")
    
    dzn_files = sorted([f for f in os.listdir(dzn_files_dir) if f.endswith('.dzn')])

    total_start_time = time.time()
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Run only instances 12, 13, and 16
    instances_to_include = [13]

    for restart in restart_values:
        restart_output_dir = os.path.join(output_dir, f"restart_{restart}")
        os.makedirs(restart_output_dir, exist_ok=True)

        print(f"\nRunning batch with restart: {restart}")

        for dzn_file in dzn_files:
            instance_number = int(''.join(filter(str.isdigit, dzn_file)))
            if instance_number not in instances_to_include:
                continue

            full_path = os.path.join(dzn_files_dir, dzn_file)
            print(f"Processing file: {full_path} with restart {restart}")

            instance = minizinc.Instance(solver, model)
            instance["restart"] = restart
            instance.add_file(full_path)

            instance_name = os.path.splitext(dzn_file)[0]
            instance_output_dir = os.path.join(restart_output_dir, instance_name)
            os.makedirs(instance_output_dir, exist_ok=True)
            output_file_path = os.path.join(instance_output_dir, f"{instance_name}.json")

            try:
                start_time = time.time()
                result = instance.solve(timeout=timedelta(seconds=timeout), all_solutions=False)
                end_time = time.time()
                runtime = end_time - start_time

                if result.status.has_solution():
                    solutions = traverse_lists(result.solution.x)
                    statistics = result.statistics

                    assignment = result.solution.x
                    max_dist = result.solution.objective
                    solution = traverse_lists(assignment)

                    output_data = {
                        "gecode": {
                            "restart": restart,
                            "time": int(runtime) if runtime < timeout else timeout,
                            "optimal": result.status == minizinc.result.Status.OPTIMAL_SOLUTION,
                            "obj": max_dist,
                            "sol": solution,
                            "runtime": str(statistics.get("time", "N/A")),
                            "initTime": str(statistics.get("initTime", "N/A")),
                            "solveTime": str(statistics.get("solveTime", "N/A")),
                            "variables": statistics.get("variables", "N/A"),
                            "propagators": statistics.get("propagators", "N/A"),
                            "propagations": statistics.get("propagations", "N/A"),
                            "nodes": statistics.get("nodes", "N/A"),
                            "failures": statistics.get("failures", "N/A"),
                            "restarts": statistics.get("restarts", "N/A"),
                            "peakDepth": statistics.get("peakDepth", "N/A"),
                            "nSolutions": statistics.get("nSolutions", "N/A")
                        }
                    }

                    with open(output_file_path, 'w') as output_file:
                        json.dump(output_data, output_file, indent=1)
                    print(f"Success: {dzn_file} with restart {restart} ran in {runtime:.2f} seconds. Objective: {max_dist}")

                else:
                    print(f"{dzn_file} with restart {restart} ran but no solution was found")
                    output_data = {
                        "gecode": {
                            "restart": restart,
                            "time": timeout,
                            "optimal": False,
                            "obj": None,
                            "sol": "NO SOLUTION FOUND"
                        }
                    }
                    with open(output_file_path, 'w') as output_file:
                        json.dump(output_data, output_file, indent=1)
            
            except minizinc.MiniZincError as e:
                print(f"MiniZincError: {dzn_file} with restart {restart} failed")
                print("Error message:\n", str(e))
            
            except Exception as e:
                print(f"General Error: {dzn_file} with restart {restart} failed")
                print("Error message:\n", str(e))

        # Run solution checker after each batch of restarts
        #print(f"\nRunning solution checker for restart {restart} results...")
        #check_solutions_with_external_script(dzn_files_dir, restart_output_dir)

    total_end_time = time.time()
    total_runtime = total_end_time - total_start_time
    print(f"\nTotal runtime for all files and restarts: {total_runtime:.2f} seconds")

def check_solutions_with_external_script(input_folder, results_folder):
    try:
        subprocess.run(["python", "solution_checker.py", input_folder, results_folder], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Solution checker failed with error: {str(e)}")

# Directories
dzn_files_dir = 'dzn_files/'
output_dir = 'res/gecode/'
model_file = './model_restart.mzn'

# Restart values to test
restart_values = [10, 15, 20, 25, 30, 35, 40, 45, 50, 1700, 1800, 1900, 2000, 2100, 2200]

# Run instances with each restart value
run_minizinc_with_restarts(dzn_files_dir, model_file, output_dir, restart_values, 300)
