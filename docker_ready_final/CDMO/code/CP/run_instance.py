import os
import time
import minizinc
import json
from datetime import timedelta
import subprocess
import argparse

def traverse_lists(lists):
    """
    This function takes in the output of the minizinc program, and returning the solution under the form of visited indices per courier.
    """
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

def save_solution(output_file_path, solver_key, new_data):
    """
    Appends or updates the solution under the specified solver key in the JSON file.
    
    Args:
        output_file_path (str): Path to the JSON file.
        solver_key (str): Key under which the solution should be stored.
        new_data (dict): New solution data to add or update.
    """
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as f:
            try:
                existing_content = json.load(f)
            except json.JSONDecodeError:
                existing_content = {} 
    else:
        existing_content = {}

    existing_content[solver_key] = new_data

    with open(output_file_path, 'w') as f:
        json.dump(existing_content, f, indent=1)


def run_minizinc_on_all(dzn_files_dir, model_file, output_dir, timeout=300, solver = "gecode", symmetry_breaking = False, relax = False, seed = 42, instance_number = -1):
    """
    Runs the MiniZinc model on all the .dzn files in the specified directory, saves the output as JSON, 
    and reports the runtime. Limits each Gecode run to a specified timeout and returns the solution or a message if unsolved.
    """
    #declare the model and solver
    model = minizinc.Model(model_file)
    chuffed = minizinc.Solver.lookup(solver)
    
    dzn_files = sorted([f for f in os.listdir(dzn_files_dir) if f.endswith('.dzn')])

    total_start_time = time.time()

    instances_to_include = list(range(1, 11)) + [13,16] #list(range(13, 22)) #

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if instance_number != -1:
        instances_to_include = list(instance_number)
    
    print(f"Running instances: {instances_to_include}")
    for dzn_file in dzn_files:

        instance_number = int(''.join(filter(str.isdigit, dzn_file)))

        #the third model should only be run on the 13 and 16 instance.
        if relax and instance_number not in [13,16]:
            continue

        if instance_number not in instances_to_include:
            continue  

        full_path = os.path.join(dzn_files_dir, dzn_file)
        print(f"\nProcessing file: {full_path}")
        instance = minizinc.Instance(chuffed, model)

        # Load data into minizinc
        instance.add_file(full_path)

        instance_name = os.path.splitext(dzn_file)[0]
        instance_output_dir = os.path.join(output_dir, instance_name)
        os.makedirs(instance_output_dir, exist_ok=True)

        # Define the JSON output file path
        output_file_path = os.path.join(instance_output_dir, f"{instance_name}.json")

        try:
            start_time = time.time()
            result = instance.solve(timeout=timedelta(seconds=timeout), random_seed = seed)
            end_time = time.time()
            runtime = end_time - start_time

            if result.status.has_solution():
                solutions = traverse_lists(result.solution.x)
                statistics = result.statistics
        
                assignment = result.solution.x
                max_dist = result.solution.objective

                solution = traverse_lists(assignment)
                solver_key = solver  
                if symmetry_breaking:
                    solver_key += "_symbreak"
                else:
                    if relax:
                        solver_key += "_symbreak_relax"

                # Create the JSON output
                output_data = {
                        "time": int(runtime) if runtime < timeout else 300,
                        "optimal": result.status == minizinc.result.Status.OPTIMAL_SOLUTION if runtime < timeout else False,
                        "obj": max_dist,
                        "sol": solution,
                }
                print(f"The output data is: \n{output_data}")
                
                # Write the JSON output to a file in the designated subdirectory
                save_solution(output_file_path, solver_key, output_data)
                
                print("Solution output saved to:", output_file_path)
            else:
                print(f"{dzn_file} ran but no solution was found within the time limit")
                output_data = {
                    "gecode": {
                        "time": 300,
                        "optimal": "False",
                        "obj": "NULL",
                        "sol": "NO SOLUTION FOUND",
                    }
                }

                print(f"The output data is: \n{output_data}")
        
        except minizinc.MiniZincError as e:
            print(f"MiniZincError: {dzn_file} failed")
            print("Error message:\n", str(e))
        
        except Exception as e:
            print(f"General Error: {dzn_file} failed")
            print("Error message:\n", str(e))
    
    # Record the end time for the entire process
    total_end_time = time.time()
    total_runtime = total_end_time - total_start_time

def check_solutions_with_external_script(input_folder, results_folder):
    """
    Calls the external solution checker script using subprocess to check all generated solutions.
    """
    try:
        subprocess.run(["python3", "../solution_checker.py", input_folder, results_folder], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Solution checker failed with error: {str(e)}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run MiniZinc instances.")
    parser.add_argument("instance", type=int, nargs="?", default=-1, help="The instance number to run (1-21). If not specified, all instances will be run.")

    args = parser.parse_args()
    instance_number = -1
    # Determine the instances to run
    if args.instance == -1:
        instance_number = -1
    elif 1 <= args.instance <= 21:
        instance_number = [args.instance]  # Run only the specified instance
    else:
        print("Error: Instance number must be between 1 and 21.")
        exit(1)

    # Directory where .dzn files are stored
    dzn_files_dir = 'dzn_files/'

    # Output directory for JSON files
    output_dir = '../res/CP/'

    solvers = ["gecode", "chuffed"] # solvers
    model_files = ['./model.mzn', './model_restart_symbreak.mzn', './model_restart_symbreak_relax.mzn'] 

    for solver in solvers:
        for model_file in model_files:
            relax= False
            symmetry_breaking = False
            if model_file == model_files[1]:
                symmetry_breaking = True
            if model_file == model_files[2]:
                relax = True
            if symmetry_breaking:
                print(f"\n\n\nUSING SOLVER: {solver}, with SB")
            else:
                print(f"\n\n\nUSING SOLVER: {solver}")
            run_minizinc_on_all(dzn_files_dir, model_file, output_dir, 300, solver = solver, symmetry_breaking = symmetry_breaking,relax =relax, instance_number = instance_number)

    dat_files_dir = '../Instances'
    check_solutions_with_external_script(dat_files_dir, output_dir)
