from z3 import *
import re
import numpy as np

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

def maxv(vs):
  m = vs[0]
  for x in vs[1:]:
    m = If(x > m, x, m)
  return m


def get_list_of_values(ll,j):
    return([If(x==j,1,0) for l in ll for x in l])


def maxdist_calc(distances, pk_bound):
    vertical_distance = np.sum(np.max(distances, axis=1))
    sorted_distance = np.sum(sorted(distances.flatten(), reverse=True)[:pk_bound+1])
    max_dist = np.min([vertical_distance, sorted_distance])

    return max_dist



def stm_model(instance, timeout, sb):
    m = instance["m"] # couriers
    n = instance["n"] # packages
    l = instance["l"] # weigths
    s = instance["s"] # sizes of couriers
    D = instance["D"] # distances
    pk_bound = n + 1

    distances = np.array(instance["D"])


    min_load = np.min(s)
    max_load = min(np.max(l), np.sum(sorted(s, reverse=True)[:pk_bound]))
    max_dist = maxdist_calc(distances, pk_bound)
    min_solution = np.max([distances[n, j] + distances[j, n] for j in range(n)])

    min_distance = min(min(distances[n][:n]), min([x[n] for x in distances[:n]]))*2

    # casting integers to z3 integers
    max_load = IntVal(f"{max_load}")
    min_load = IntVal(f"{min_load}")
    max_dist = IntVal(f"{max_dist}")
    min_solution = IntVal(f"{min_solution}")

    o = Optimize()

    # main decision variable: x[i,k] = j mean that the i-th courier is in j at pk_bound k
    x = [[Int(f'x_{i}_{k}') for k in range(0,pk_bound+1)]for i in range(m)]

    # variable for distance calculation
    y = [Int(f'y_{i}') for i in range(m)] 

    # variable for loads calculation
    load = [Int(f'load_{i}') for i in range(m)] 

    # distance to minimize
    max_distance = Int(f'max_distance')
    


    # we define distances as a z3 array because it is easier to indicize
    distances = Array('distances', IntSort(), ArraySort(IntSort(), IntSort()))
    for j in range(n+1):
        for j1 in range(n+1):
            o.add(distances[j][j1] == instance['D'][j][j1])

    # we define s as a z3 array because it is easier to indicize
    s = Array('s', IntSort(), IntSort())
    for j in range(n):
        o.add(s[j] == instance['s'][j])
    o.add(s[n] == 0)

    
    ####################################### CONSTRAINTS #######################################

    # define possible value for x[i][k]
    o.add([And(x[i][k] >= 0, x[i][k] <= n) for i in range(m) for k in range(1,pk_bound)])
    o.add([And(x[i][0] == n, x[i][pk_bound] == n) for i in range(m)])

    # for each i foreach k, each x[i][k] must be different, unless it is equal to n.
    for j in range(n):
        o.add([Sum(get_list_of_values([[x[i][k] for k in range(1,pk_bound+1)] for i in range(m)],j))==1])
    
    # for each i, the sum of the weights of the packages carried by the courier i must be less than the capacity of the courier i
    for i in range(m):
        o.add(load[i] == Sum([s[x[i][k]] for k in range(1,pk_bound)]))
        o.add(load[i] <= l[i])
    
    # bound to loads array
    for i in range(m):
        o.add(And(load[i] >= min_load, load[i] <= max_load))

    # Total items size less than total couriers capacity
    o.add(Sum([load[i] for i in range(m)]) >= Sum([s[j] for j in range(n)]))




    ####################################### SYMMETRY BREAKING CONSTRAINTS #######################################
    if sb:
        # once a courier i return to the depot, it cant deliver other packages
        for i in range(m):
            for k in range(1,pk_bound):
                o.add(Implies(x[i][k]==n, x[i][k+1]==n))
        
        # lexycographic constraint between couriers with == capacity
        for i1 in range(m-1):
            for i2 in range(i1+1,m):
                o.add(Implies(l[i1]==l[i2], If(x[i1][1]!=n, x[i1][1], -1)<=If(x[i1][1]!=n, x[i1][1], -1)))
        
        # constraint over maximum loads of the couriers
        for i1 in range(m-1):
            for i2 in range(i1+1,m):
                o.add(Implies(l[i1] <= l[i2], load[i1] <= load[i2]))
    

    ####################################### OBJECTIVE FUNCTION #######################################
    
    # distances array
    for i in range(m):
        o.add(y[i] == Sum([distances[x[i][k]][x[i][k+1]] for k in range(0,pk_bound)]))

    #bound to distances array
    for i in range(m):
        o.add(And(y[i] >= IntVal(f"{min_distance}"), y[i] <= max_dist))

    # variable to minimize
    o.add(max_distance == maxv(y))

    # bound the variable to minimize
    o.add(max_distance >= min_solution)

    return o, x, max_distance

    

def format_solution(instance, model, x):
    m = instance['m'] # couriers
    n = instance['n'] # packages
    print(model)
    pk_bound = n-1 # max number of packages a courier can carry
    step_courier = []
    for i in range(m):
        step_courier.append([])
        for k in range(1,pk_bound+1):
            if model.eval(x[i][k]).as_long() != n:
                step_courier[i].append(model.eval(x[i][k]).as_long() + 1) 
    return step_courier


