from SMT_model import *
from time import time as time_clock
from z3 import IntNumRef
import json
import subprocess

timeout = 300

def run_smt(instance, timeout, sb=False):
    generation_start_time = time_clock()

    # Build the SMT model
    o, x, max_distance = stm_model(instance, sb)
    generation_duration = time_clock() - generation_start_time
    o.set("timeout", int(timeout - generation_duration) * 1000)

    # Minimize the objective
    obj = o.minimize(max_distance)
    res = o.check()  # Check satisfiability
    final_time = int(time_clock() - generation_start_time)

    if res == sat:
        try:
            # Format the solution if satisfiable
            result_formatted = format_solution(instance, o.model(), x)
            return result_formatted, True, obj.value(), final_time
        except Exception as e:
            return str(e), False, obj.value()
    elif res == unknown:
        try:
            model = o.model()
            if model:  # Check if a model exists
                # Format the partial solution
                result_formatted = format_solution(instance, model, x)
                best_objective = model.eval(max_distance, model_completion=True)
                return (
                    result_formatted,
                    False,
                    best_objective.as_long() if best_objective.is_int() else float(best_objective.as_decimal(5)),
                    final_time
                )
            else:
                # No model available, return fallback message
                return "No solution found", False, None
        except Exception as e:
            return f"unknown\nError retrieving model: {e}", False, None
    elif res == unsat:
        return "unsat", False, None
    else:
        return "unknown", False, None
    
def all_solutions(solvers, solutions):
    def convert(obj):
        if isinstance(obj, IntNumRef):
            return obj.as_long()
        if isinstance(obj, list):
            return [convert(i) for i in obj]
        return obj
    
    output_data = {}
    sol_index=0
    for solver in solvers:
        solution = solutions[sol_index]
        if solution == "unsat":
            print("Problem is unsatisfiable for solver", solver)
        elif solution == "unknown":
            print("Problem is unknown for solver", solver)
        elif solution[0] == "No solution found":
            print("No solution found for solver", solver)
        else:
            output_data.update({
                solver:
                    {
                    "time": convert(solution[3]),
                    "optimal": convert(solution[1]),
                    "obj": convert(solution[2]),
                    "sol": convert(solution[0])
                    }
                })
        sol_index += 1
        
    return output_data

def save_solution(solvers ,solutions, path):
    output_data = all_solutions(solvers, solutions)
    with open(path, 'w') as file:
        if output_data != []:
            print(output_data)
            json.dump(output_data, file, indent=4)
            
#Run the SMT model for all the instances and saves the solutions in json files.
def run_all_instances():
    for i in range(1, 11):
        if i < 10:
            Path = f'../Instances/inst0{i}.dat'
        else:
            Path = f'../Instances/inst{i}.dat'

        with open(Path, 'r') as file:
            data = file.read()
        instance = data_parsing(data)
        solution_smt = run_smt(instance, timeout, False)
        solution_smt_sb = run_smt(instance, timeout, True)
        if i < 10:
            save_solution(["smt", "smt_sb"], [solution_smt, solution_smt_sb], f'res/SMT/inst0{i}/inst0{i}.json')
        else:
            save_solution(["smt", "smt_sb"], [solution_smt, solution_smt_sb], f'res/SMT/inst{i}/inst{i}.json')
        
        
def check_solutions_with_external_script(input_folder, results_folder):
    """
    Calls the external solution checker script using subprocess to check all generated solutions.
    """
    try:
        # Call the solution checker, passing the input folder and results folder
        subprocess.run(["python", "solution_checker.py", input_folder, results_folder], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Solution checker failed with error: {str(e)}")
        
run_all_instances()

# Directory where dat files are stored
instance_dir = '../Instances'  

# Output directory for JSON files
output_dir = 'res/SMT/'

check_solutions_with_external_script(instance_dir, output_dir)  