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
        current_index = n  # Start from the last index (n)
        visited = []  # To memorize the traversal order

        if not lst:  # If the list is empty, append an empty list
            solution.append([])
            continue
        
        if lst == list(range(1, len(lst) + 1)):
            solution.append([])
            continue

        # Traverse the list until the current index is equal to its value
        while lst[current_index - 1] != n:
            if current_index != n:
                visited.append(current_index)
            current_index = lst[current_index - 1]  # Move to the index given by the value at the current position

        # Append the last index where current_index == lst[current_index - 1]
        visited.append(current_index)

        solution.append(visited)
    return solution

def run_minizinc_on_all(dzn_files_dir, model_file, output_dir, timeout=300):
    """
    Runs the MiniZinc model on all the .dzn files in the specified directory, saves the output as JSON, 
    and reports the runtime. Limits each Gecode run to a specified timeout and returns the solution or a message if unsolved.
    """
    # Initialize MiniZinc model and configure solver
    model = minizinc.Model(model_file)
    chuffed = minizinc.Solver.lookup("gecode")
    
    # Find all .dzn files in the specified directory
    dzn_files = sorted([f for f in os.listdir(dzn_files_dir) if f.endswith('.dzn')])

    # Record the start time for the entire process
    total_start_time = time.time()

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    instances_to_include = list(range(1, 11))+ [13,16] #list(range(13, 22))

    #instances_to_include = [16] #list(range(13, 22))


    for dzn_file in dzn_files:
        # Extract the instance number from the file name
        instance_number = int(''.join(filter(str.isdigit, dzn_file)))
        
        # Check if the instance number is in the list of desired instances
        if instance_number not in instances_to_include:
            continue  # Skip files that are not in the specified instances

        full_path = os.path.join(dzn_files_dir, dzn_file)
        print(f"\nProcessing file: {full_path}")
        instance = minizinc.Instance(chuffed, model)

        # Load the .dzn data file into the instance
        instance.add_file(full_path)

        # Create a subdirectory for the output JSON file
        instance_name = os.path.splitext(dzn_file)[0]  # Get the name without the extension (e.g., 'inst01')
        instance_output_dir = os.path.join(output_dir, instance_name)
        os.makedirs(instance_output_dir, exist_ok=True)

        # Define the JSON output file path
        output_file_path = os.path.join(instance_output_dir, f"{instance_name}.json")

        # Solve the instance with a timeout
        try:
            start_time = time.time()
            result = instance.solve(timeout=timedelta(seconds=timeout))
            end_time = time.time()
            runtime = end_time - start_time

            if result.status.has_solution():
                solutions = traverse_lists(result.solution.x)
                statistics = result.statistics
        

                #break
                assignment = result.solution.x
                max_dist = result.solution.objective

                # Transform the assignment `x` to the solution format
                solution = traverse_lists(assignment)

                # Create the JSON output in the required format
                output_data = {
                    "gecode": {
                        "time": int(runtime) if runtime < timeout else timeout,
                        "optimal": result.status == minizinc.result.Status.OPTIMAL_SOLUTION if runtime < timeout else "False",
                        "obj": max_dist,
                        "sol": solution,
                    }
                }

                print(f"The output data is: \n{output_data}")
                
                # Join the `sol` list into a string manually to avoid line breaks
                #output_data["gecode"]["sol"] = json.dumps(output_data["gecode"]["sol"]).replace('\n', '')

                # Write the JSON output to a file in the designated subdirectory
                with open(output_file_path, 'w') as output_file:
                    json.dump(output_data, output_file, indent=1)
                
                print(f"Success: {dzn_file} ran in {runtime:.2f} seconds")
                print("Solution output saved to:", output_file_path)
            else:
                print(f"{dzn_file} ran but no solution was found within the time limit")
                output_data = {
                    "gecode": {
                        "time": 300,
                        "optimal": "FALSE",
                        "obj": "NULL",
                        "sol": "NO SOLUTION FOUND",
                    }
                }

                print(f"The output data is: \n{output_data}")
                
                # Write the JSON output to a file in the designated subdirectory
                with open(output_file_path, 'w') as output_file:
                    json.dump(output_data, output_file, indent, sort_keys=True)
                    #json.dump(output_data, output_file)                
                print("Solution output saved to:", output_file_path)
        
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

def check_solutions_with_external_script(input_folder, results_folder):
    """
    Calls the external solution checker script using subprocess to check all generated solutions.
    """
    try:
        # Call the solution checker, passing the input folder and results folder
        subprocess.run(["python", "solution_checker.py", input_folder, results_folder], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Solution checker failed with error: {str(e)}")

# Directory where .dzn files are stored
dzn_files_dir = 'dzn_files/'  # Modify this to the directory containing the .dzn files

# Output directory for JSON files
output_dir = 'res/CP/'  # Modify this as needed

# MiniZinc model file
model_file = './model.mzn'  # Modify this to the path of your MiniZinc model file

# Run the MiniZinc model on all .dzn files
# Uncomment the next line to run the instances and automatically save in separate folders
run_minizinc_on_all(dzn_files_dir, model_file, output_dir, 300)

# Call the external solution checker script to validate the outputs
# Pass the output directory directly (as JSON files are stored there)
dat_files_dir = '../Instances'
check_solutions_with_external_script(dat_files_dir, output_dir)
