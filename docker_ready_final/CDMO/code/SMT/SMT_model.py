from z3 import *
import re
import numpy as np

# Parse the data from the file, to get the number of couriers, packages, weights, sizes and distances as matrices
# computable by the model
def data_parsing(data):
    text = data.split("\n")
    fixed_re = r"(\d+)" 
    text = [c for c in text if c != ""]
    text = [c.strip() for c in text]
    
    m = int(re.findall(fixed_re, text[0])[0])
    n = int(re.findall(fixed_re, text[1])[0])
    l = [int(c) for c in re.findall(fixed_re, text[2])]
    s = [int(c) for c in re.findall(fixed_re, text[3])]
    D = []
    for i in range(4, 4 + n + 1):
        D.append([int(c) for c in re.findall(fixed_re, text[i])])

    return {
        "m": m,
        "n": n,
        "l": l,
        "s": s,
        "D": D,
    }

# Custom function to get the maximum value of a list of values
def max_comparison(value):
    m = value[0]
    for i in value[1:]:
        m = If(i > m, i, m)
    return m


def get_list_of_values(lst, j):
    return [If(i == j, 1, 0) for l in lst for i in l]

# Custom function to calculate the maximum distance a courier can travel
def maxdist_calc(dist, pk_bound):
    vertical_dist = np.sum(np.max(dist, axis=1))
    sorted_dist = np.sum(sorted(dist.flatten(), reverse=True)[: pk_bound + 1])
    max_dist = np.min([vertical_dist, sorted_dist])

    return max_dist


def smt_model(instance, sb):
    m = instance["m"]  # couriers
    n = instance["n"]  # packages
    l = instance["l"]  # loads of couriers
    s = instance["s"]  # sizes of couriers
    dist = np.array(instance["D"])
    
    pk_bound = n # max number of packages a courier can carry
    
    # Calculate the minimum and maximum values for the decision variables
    min_l = np.min(s)
    max_l = min(np.max(l), np.sum(sorted(s, reverse=True)[:pk_bound]))
    max_dist = maxdist_calc(dist, pk_bound)
    lower_bound = np.max([dist[n, j] + dist[j, n] for j in range(n)])
    upper_bound = np.sum(np.max(dist, axis=1))
    
    # Cast the values to z3 IntVal
    max_l = IntVal(f"{max_l}")
    min_l = IntVal(f"{min_l}")
    max_dist = IntVal(f"{max_dist}")
    lower_bound = IntVal(f"{lower_bound}")
    upper_bound = IntVal(f"{upper_bound}")
    

    z3_optimizer = Optimize()
    
    #Decision variables

    # Main decision variables: position_matrix[i][k] are the packages carried by courier i in the k-th step
    position_matrix = [
        [Int(f"position_matrix_{i}_{k}") for k in range(0, pk_bound + 1)]
        for i in range(m)
    ]

    # This variable is used to store the load of each courier
    load = [Int(f"load_{i}") for i in range(m)]

    # This variable is used to store the distance travelled by each courier
    cour_dists = [Int(f"cour_dists_{i}") for i in range(m)]

    # The value to minimize
    max_dist = Int(f"max_dist")

    # We need to indicize the distances array to be able to use it in the model
    dist = Array("dist", IntSort(), ArraySort(IntSort(), IntSort()))
    for j in range(n + 1):
        for j1 in range(n + 1):
            z3_optimizer.add(dist[j][j1] == instance["D"][j][j1])

    # Define s as a z3 array
    s = Array("s", IntSort(), IntSort())
    for j in range(n):
        z3_optimizer.add(s[j] == instance["s"][j])
    z3_optimizer.add(s[n] == 0)

    #Constraints

    # Possible values for position_matrix[i][k] are between 0 and n
    z3_optimizer.add(
        [
            And(position_matrix[i][k] >= 0, position_matrix[i][k] <= n)
            for i in range(m)
            for k in range(1, pk_bound)
        ]
    )
    z3_optimizer.add([And(position_matrix[i][0] == n, position_matrix[i][pk_bound] == n) for i in range(m)])

    # Each position in the array must be different, unless it is the last one
    for j in range(n):
        z3_optimizer.add(
            [
                Sum(
                    get_list_of_values(
                        [[position_matrix[i][k] for k in range(1, pk_bound + 1)] for i in range(m)],
                        j,
                    )
                )
                == 1
            ]
        )

    # For each courier, their maximum load must be respected given the sum of the packages they carry
    for i in range(m):
        z3_optimizer.add(load[i] == Sum([s[position_matrix[i][k]] for k in range(1, pk_bound)]))
        z3_optimizer.add(load[i] <= l[i])

    # The loads must be in range
    for i in range(m):
        z3_optimizer.add(And(load[i] >= min_l, load[i] <= max_l))

    # Total items size less than total couriers capacity
    z3_optimizer.add(Sum([load[i] for i in range(m)]) >= Sum([s[j] for j in range(n)]))
    
    # Once a courier returns to the depot, it can't deliver other packages
    for i in range(m):
        for k in range(1, pk_bound):
            z3_optimizer.add(Implies(position_matrix[i][k] == n, position_matrix[i][k + 1] == n))

    # Symmetry breaking constraint
    
    if sb:
        # Lexycographic constraint between couriers with the same capacity
        for i1 in range(m - 1):
            for i2 in range(i1 + 1, m):
                z3_optimizer.add(
                    Implies(
                        l[i1] == l[i2],
                        If(position_matrix[i1][1] != n, position_matrix[i1][1], -1)
                        <= If(position_matrix[i1][1] != n, position_matrix[i1][1], -1),
                    )
                )
        
    # Reach objective function

    #Add distance travelled by each courier
    for i in range(m):
        z3_optimizer.add(cour_dists[i] == Sum([dist[position_matrix[i][k]][position_matrix[i][k + 1]] for k in range(0, pk_bound)]))

    # Add constraint that each distance travelled by a courier must be less than the maximum distance
    for i in range(m):
        z3_optimizer.add(cour_dists[i] <= max_dist)

    # Set the minimization objective
    z3_optimizer.add(max_dist == max_comparison(cour_dists))

    # Set the lower bound for the objective
    z3_optimizer.add(max_dist >= lower_bound, max_dist <= upper_bound)

    return z3_optimizer, position_matrix, max_dist


def get_sol(instance, model, position_matrix):
    m = instance["m"]
    n = instance["n"]  
    pk_bound = n  
    next_step = []
    for i in range(m):
        next_step.append([])
        for j in range(1, pk_bound):
            if model.eval(position_matrix[i][j]).as_long() != n:
                next_step[i].append(model.eval(position_matrix[i][j]).as_long() + 1)
    return next_step
