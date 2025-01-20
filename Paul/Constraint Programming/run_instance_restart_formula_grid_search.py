import os
import time
import minizinc
import json
from datetime import timedelta
import subprocess

def extract_number(string):
    """
    Extracts the number from a string of the format 'key = value;'
    and returns it as an integer.
    """
    try:
        # Split by '=' and strip whitespace
        key, value = string.split("=")
        # Remove the trailing semicolon and convert to integer
        return int(value.strip().rstrip(";"))
    except ValueError:
        raise ValueError(f"Invalid format: {string}")

def parse_dzn(file_path):
    """
    Parses a .dzn file with positional parameter values instead of key-value pairs.
    Assumes specific lines correspond to specific parameters.
    """
    params = {}
    #print("test param 1")
    with open(file_path, "r") as file:
        lines = [line.strip() for line in file if line.strip() and not line.startswith("%")]
    # Assuming the file format:
    # Line 1: n (number of couriers)
    # Line 2: m (number of distribution points)
    # Line 3: Other parameters like vehicle capacities or demand
    params["n"] = extract_number(lines[0])  # First line is `n`
    params["m"] = extract_number(lines[1])    # Second line is `m`
    params["n"] = int(params["n"])
    params["m"] = int(params["m"])
    #print(type(params["n"]),params["n"])
    #print("test param 12")
    #params["other"] = [list(map(int, line.split())) for line in lines[2:]]  # Remaining lines are arrays
    #exit()
    return params



def run_minizinc_grid_search(dzn_files_dir, model_file, output_dir, formulas, timeout=300):
    """
    Runs a grid search over different restart formulas for the MiniZinc model, saves results in a .txt file, 
    and outputs the number of successful instances per formula, along with n, m, and the formula.
    Logs success and failure messages into a separate log file.
    Passes the restart parameter directly to the MiniZinc model.
    """
    # Initialize MiniZinc model and configure solver
    model = minizinc.Model(model_file)
    chuffed = minizinc.Solver.lookup("gecode")

    print("Script starting....")

    # Find all .dzn files in the specified directory
    dzn_files = sorted([f for f in os.listdir(dzn_files_dir) if f.endswith('.dzn')])

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Instances to include in the grid search
    instances_to_include = [11, 12, 13, 16, 19, 21]#list(range(11, 23))

    # Text file to save grid search results
    results_file = os.path.join(output_dir, "grid_search_results.txt")
    log_file = os.path.join(output_dir, "grid_search_log.txt")

    # Open the results and log files in write mode
    with open(results_file, "w") as results, open(log_file, "w") as logs:
        results.write("Formula, Instances Solved, Details (n, m, formula)\n")

        # Iterate over formulas
        for formula_name, formula_func in formulas.items():
            solved_instances = 0
            details = []
            #print("test")
            results.write(f"\nTesting formula: {formula_name}\n")

            # Record the start time for the formula
            formula_start_time = time.time()

            for dzn_file in dzn_files:
                #print("test2")
                # Extract the instance number from the file name
                instance_number = int(''.join(filter(str.isdigit, dzn_file)))

                # Check if the instance number is in the list of desired instances
                if instance_number not in instances_to_include:
                    continue

                full_path = os.path.join(dzn_files_dir, dzn_file)
                logs.write(f"\nProcessing file: {full_path} with formula: {formula_name}\n")

                instance = minizinc.Instance(chuffed, model)
                
                # Load the .dzn data file into the instance
                instance.add_file(full_path)
                #print("test3")
                try:
                    # Parse parameters from the .dzn file
                    params = parse_dzn(full_path)
                    #print("test4")
                    n = params["n"]
                    m = params["m"]
                    #print("test5")
                    #print(f"n is {n}")

                    if not isinstance(n, int) or not isinstance(m, int):
                        raise ValueError(f"Invalid values for n or m in file {full_path}: n={n}, m={m}")

                    restarts = formula_func(n, m)
                    restart = int(restarts)

                    # Pass the restart parameter to the model
                    instance["restarts"] = restarts

                    # Solve the instance with a timeout
                    start_time = time.time()
                    result = instance.solve(timeout=timedelta(seconds=timeout))
                    end_time = time.time()
                    runtime = end_time - start_time
                    if result.status.has_solution():
                        solved_instances += 1
                        details.append((n, m, formula_name))
                        logs.write(f"Success: {dzn_file} solved in {runtime:.2f} seconds with restarts={restarts}\n")
                    else:
                        logs.write(f"{dzn_file} ran but no solution was found within the time limit with restarts={restarts}\n")

                except minizinc.MiniZincError as e:
                    logs.write(f"MiniZincError: {dzn_file} failed with formula: {formula_name}\n")
                    logs.write(f"Error message:\n{str(e)}\n")

                except Exception as e:
                    logs.write(f"General Error: {dzn_file} failed with formula: {formula_name}\n")
                    logs.write(f"Error message:\n{str(e)}\n")

                results.flush()
                logs.flush()

            # Record the end time for the formula
            formula_end_time = time.time()
            formula_runtime = formula_end_time - formula_start_time

            # Write results for the formula
            results.write(f"{formula_name}, {solved_instances}, {details}\n")
            results.write(f"Runtime for formula {formula_name}: {formula_runtime:.2f} seconds\n")

            results.flush()
            logs.flush()

    print(f"Grid search completed. Results saved to: {results_file}")
    print(f"Log saved to: {log_file}")

# Directory where .dzn files are stored
dzn_files_dir = 'dzn_files/'  # Modify this to the directory containing the .dzn files

# Output directory for JSON files
output_dir = 'res/grid_search_test2/'  # Modify this as needed

# MiniZinc model file
model_file = './model_grids.mzn'  # Modify this to the path of your MiniZinc model file

# Define the formulas for restarts
formulas = {
    "n": lambda n, m: n,
    "m": lambda n, m: m,
    "n*m": lambda n, m: n * m,
    "n+m": lambda n, m: n + m,
    "2*n": lambda n, m: 2 * n,
    "2*m": lambda n, m: 2 * m,
    "2*n*m": lambda n, m: 2 * n * m,
    "2*(n+m)": lambda n, m: 2 * (n + m),
    "5*n": lambda n, m: 5 * n,
    "5*m": lambda n, m: 5 * m,
    "5*n*m": lambda n, m: 5 * n * m,
    "5*(n+m)": lambda n, m: 5 * (n + m)
}

# Run the grid search
run_minizinc_grid_search(dzn_files_dir, model_file, output_dir, formulas, timeout=300)
