import numpy as np
from z3 import *

from .utils import *


def mcp_pb(instance):
    m = instance["m"] # courriers
    n = instance["n"] # packages
    l = instance["l"] # weigths
    s = instance["s"] # sizes of courriers
    time = 4
    min_load = instance["min_load"] # min load of each courrier
    max_load = instance["max_load"] # max load of each courrier

    solver = Solver()

    # To codify that courrier i deliver package j at time k
    v = [[[Bool(f"x_{i}_{j}_{k}") for k in range(time+1)] for j in range (n+1)] for i in range(m)]

    d = [[[Bool(f"d_{i}_{start}_{end}") for end in range(n+1)]
          for start in range(n+1)] for i in range(m)]

    for i in range(m):
        for k in range(time):
            for startj in range(n+1):
                for endj in range(n+1):
                    solver.add(
                        Implies(And(v[i][startj][k], v[i][endj][k+1]), d[i][startj][endj])
                    )

    # Constraints
    # 1. Each courier can carry at most l[i] kg
    # Pb version
    for i in range(m):
       solver.append(PbLe([(v[i][j][k],s[j]) for j in range(n) for k in range(1,time)], min(l[i], max_load)))
       solver.append(PbGe([(v[i][j][k],s[j]) for j in range(n) for k in range(1,time)], min_load))


    # 2. Each courier i starts and ends at position j = n
    for i in range(m):
        # solver.add(And(v[i][n][0], v[i][n][time]))
        solver.add(v[i][n][0])
        solver.add(v[i][n][time])


    # 3. Each courier can't be in two places at the same time 
    for i in range(m):
        for k in range(time+1):
            solver.add(exactly_one_seq([v[i][j][k] for j in range(n+1)], f"amo_package_{k}_{i}")) #(PbEq([(v[i][j][k],1) for j in range(n+1)],1))
    
    # 4. Each package j is delivered exactly once
    for j in range(n):
        solver.add(exactly_one_seq([v[i][j][k] for k in range(1,time) for i in range(m)], f"exactly_once_{j}")) #(PbEq([(v[i][j][k],1) for k in range(1,n+1) for i in range(m)],1))    

    return solver, v, d