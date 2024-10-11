import os
import time
import minizinc
import json
from datetime import timedelta

def run_minizinc_on_all(dzn_files_dir, model_file, output_dir, timeout=300):
    """
    Runs the MiniZinc model on all the .dzn files in the specified directory, saves the output as JSON, 
    and reports the runtime. Limits each Gecode run to a specified timeout and returns the solution or a message if unsolved.
    """
    # Initialize MiniZinc model and configure solver
    model = minizinc.Model(model_file)
    gecode = minizinc.Solver.lookup("gecode")
    
    # Find all .dzn files in the specified directory
    dzn_files = [f for f in os.listdir(dzn_files_dir) if f.endswith('.dzn')]

    # Record the start time for the entire process
    total_start_time = time.time()

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for dzn_file in dzn_files:
        full_path = os.path.join(dzn_files_dir, dzn_file)
        print(f"Processing file: {full_path}")
        instance = minizinc.Instance(gecode, model)

        # Load the .dzn data file into the instance
        instance.add_file(full_path)

        # Record start time for the individual file
        start_time = time.time()
        
        # Solve the instance with a timeout
        try:
            result = instance.solve(timeout=timedelta(seconds=timeout))
            end_time = time.time()
            runtime = end_time - start_time

            if result.status.has_solution():
                # Parse output to match required JSON structure
                assignment = result.solution.x
                max_dist = result.solution.objective

                # Transform the assignment `x` to the solution format
                solution = []
                for i in range(len(assignment)):
                    courier_items = [j + 1 for j in range(len(assignment[i])) if assignment[i][j]]
                    solution.append(courier_items)
                
                # Create the JSON output in the required format
                output_data = {
                    "gecode": {
                        "time": int(runtime) if runtime < timeout else timeout,
                        "optimal": result.status == minizinc.result.Status.SATISFIED,
                        "obj": max_dist,
                        "sol": solution
                    }
                }

                print(f"\nThe output data is: \n{output_data}")
                
                # Write the JSON output to a file
                output_file_path = os.path.join(output_dir, f"{os.path.splitext(dzn_file)[0]}.json")
                with open(output_file_path, 'w') as output_file:
                    json.dump(output_data, output_file, indent=4)
                
                print(f"Success: {dzn_file} ran in {runtime:.2f} seconds")
                print("Solution output saved to:", output_file_path)
            else:
                print(f"{dzn_file} ran but no solution was found within the time limit")
        
        except minizinc.MiniZincError as e:
            print(f"MiniZincError: {dzn_file} failed")
            print("Error message:\n", str(e))
        
        except Exception as e:
            print(f"General Error: {dzn_file} failed")
            print("Error message:\n", str(e))
    
    # Record the end time for the entire process
    total_end_time = time.time()
    total_runtime = total_end_time - total_start_time

    # Report the total runtime
    print(f"\nTotal runtime for all files: {total_runtime:.2f} seconds")

# Directory where .dzn files are stored
dzn_files_dir = 'dzn_files/'  # Modify this to the directory containing the .dzn files

# Output directory for JSON files
output_dir = 'res/gecode/'  # Modify this as needed

# MiniZinc model file
model_file = './model.mzn'  # Modify this to the path of your MiniZinc model file

# Run the MiniZinc model on all .dzn files
run_minizinc_on_all(dzn_files_dir, model_file, output_dir, 300)
