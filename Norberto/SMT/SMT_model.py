from z3 import *
import re
import numpy as np

# Parse the data from the file, to get the number of couriers, packages, weights, sizes and distances as matrices
# computable by the model
def data_parsing(data):
    text = data.split("\n")
    num_reg = r"(\d+)"
    text = [x for x in text if x != ""]
    text = [x.strip() for x in text]
    m = int(re.findall(num_reg, text[0])[0])
    n = int(re.findall(num_reg, text[1])[0])
    l = [int(x) for x in re.findall(num_reg, text[2])]
    s = [int(x) for x in re.findall(num_reg, text[3])]

    D = []
    for i in range(4, 4 + n + 1):
        D.append([int(x) for x in re.findall(num_reg, text[i])])

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
    for x in value[1:]:
        m = If(x > m, x, m)
    return m


def get_list_of_values(ll, j):
    return [If(x == j, 1, 0) for l in ll for x in l]

# Custom function to calculate the maximum distance a courier can travel
def maxdist_calc(distances, pk_bound):
    vertical_distance = np.sum(np.max(distances, axis=1))
    sorted_distance = np.sum(sorted(distances.flatten(), reverse=True)[: pk_bound + 1])
    max_dist = np.min([vertical_distance, sorted_distance])

    return max_dist


def stm_model(instance, sb):
    m = instance["m"]  # couriers
    n = instance["n"]  # packages
    l = instance["l"]  # loads of couriers
    s = instance["s"]  # sizes of couriers
    pk_bound = n # max number of packages a courier can carry

    distances = np.array(instance["D"])
    
    # Calculate the minimum and maximum values for the decision variables
    min_load = np.min(s)
    max_load = min(np.max(l), np.sum(sorted(s, reverse=True)[:pk_bound]))
    max_dist = maxdist_calc(distances, pk_bound)
    min_solution = np.max([distances[n, j] + distances[j, n] for j in range(n)])
    
    # Cast the values to z3 IntVal
    max_load = IntVal(f"{max_load}")
    min_load = IntVal(f"{min_load}")
    max_dist = IntVal(f"{max_dist}")
    min_solution = IntVal(f"{min_solution}")

    o = Optimize()
    
    #Decision variables

    # Main decision variables: x[i][k] are the packages carried by courier i in the k-th step
    x = [
        [Int(f"x_{i}_{k}") for k in range(0, pk_bound + 1)]
        for i in range(m)
    ]

    # This variable is used to store the distance travelled by each courier
    y = [Int(f"y_{i}") for i in range(m)]

    # This variable is used to store the load of each courier
    load = [Int(f"load_{i}") for i in range(m)]

    # The value to minimize
    max_distance = Int(f"max_distance")

    # We need to indicize the distances array to be able to use it in the model
    distances = Array("distances", IntSort(), ArraySort(IntSort(), IntSort()))
    for j in range(n + 1):
        for j1 in range(n + 1):
            o.add(distances[j][j1] == instance["D"][j][j1])

    # we define s as a z3 array because it is easier to indicize
    s = Array("s", IntSort(), IntSort())
    for j in range(n):
        o.add(s[j] == instance["s"][j])
    o.add(s[n] == 0)

    #Constraints

    # Possible values for x[i][k] are between 0 and n
    o.add(
        [
            And(x[i][k] >= 0, x[i][k] <= n)
            for i in range(m)
            for k in range(1, pk_bound)
        ]
    )
    o.add([And(x[i][0] == n, x[i][pk_bound] == n) for i in range(m)])

    # Each position in the array must be different, unless it is the last one
    for j in range(n):
        o.add(
            [
                Sum(
                    get_list_of_values(
                        [[x[i][k] for k in range(1, pk_bound + 1)] for i in range(m)],
                        j,
                    )
                )
                == 1
            ]
        )

    # For each courier, their maximum load must be respected given the sum of the packages they carry
    for i in range(m):
        o.add(load[i] == Sum([s[x[i][k]] for k in range(1, pk_bound)]))
        o.add(load[i] <= l[i])

    # The loads must be in range
    for i in range(m):
        o.add(And(load[i] >= min_load, load[i] <= max_load))

    # Total items size less than total couriers capacity
    o.add(Sum([load[i] for i in range(m)]) >= Sum([s[j] for j in range(n)]))

    # Symmetry breaking constraints
    
    if sb:
        # Once a courier returns to the depot, it cant deliver other packages
        for i in range(m):
            for k in range(1, pk_bound):
                o.add(Implies(x[i][k] == n, x[i][k + 1] == n))

        # Lexycographic constraint between couriers with the same capacity
        for i1 in range(m - 1):
            for i2 in range(i1 + 1, m):
                o.add(
                    Implies(
                        l[i1] == l[i2],
                        If(x[i1][1] != n, x[i1][1], -1)
                        <= If(x[i1][1] != n, x[i1][1], -1),
                    )
                )
        
    # Reach objective function

    # distances array
    for i in range(m):
        o.add(y[i] == Sum([distances[x[i][k]][x[i][k + 1]] for k in range(0, pk_bound)]))

    # bound to distances array
    for i in range(m):
        o.add(y[i] <= max_dist)

    # variable to minimize
    o.add(max_distance == max_comparison(y))

    # bound the variable to minimize
    o.add(max_distance >= min_solution)

    return o, x, max_distance


def format_solution(instance, model, x):
    m = instance["m"]  # couriers
    n = instance["n"]  # packages
    pk_bound = n  # max number of packages a courier can carry
    step_courier = []
    for i in range(m):
        step_courier.append([])
        for k in range(1, pk_bound):
            if model.eval(x[i][k]).as_long() != n:
                step_courier[i].append(model.eval(x[i][k]).as_long() + 1)
    return step_courier
