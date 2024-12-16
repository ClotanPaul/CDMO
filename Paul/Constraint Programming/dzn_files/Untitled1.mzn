include "globals.mzn";
include "gecode.mzn";

% Parameters
int: m;                          % number of couriers
int: n;                          % number of distribution points
array[1..m] of int: l;           % vehicle capacities
array[1..n] of int: s;           % demand of each distribution point
array[1..n+1, 1..n+1] of int: D; % distance matrix (n+1 corresponds to the origin)

% Sets
set of int: COURIERS = 1..m;
set of int: ITEMS = 1..n;
set of int: NODES = 1..n + 1;    % Including depot as node n+1

% Decision Variables
array[COURIERS, NODES] of var NODES: x; % x[i, j] = k means courier i goes from node j to node k
array[ITEMS] of var COURIERS: loads;     % loads[j] = i means item j is assigned to courier i

array[COURIERS] of var 0..sum(s): y;    % y[i] is the total distance traveled by courier i

% Lower and Upper Bounds for traveled_max_dist
int: obj_lowerbound = max([D[n+1, i] + D[i, n+1] | i in ITEMS]);  % Minimum round-trip distance to any point
array[ITEMS] of int: max_dists = [max([D[i, j] | j in 1..n+1]) | i in ITEMS];
int: obj_upperbound = sum(max_dists) + max([D[n+1, i] | i in ITEMS]) + max([D[i, n+1] | i in ITEMS]);

% Objective Variable with Bounds
var obj_lowerbound..obj_upperbound: traveled_max_dist;

% Objective: Minimize the maximum travel distance
constraint
    forall(i in COURIERS) (
        y[i] = sum([if x[i, j] != j then D[j, x[i, j]] else 0 endif | j in NODES])
    );
constraint
    traveled_max_dist = max(y);

% Bin Packing Constraint
constraint
    bin_packing_capa(l, loads, s);

% Synchronize Loads and Routing
constraint
    forall(j in ITEMS)(
        exists(i in COURIERS)(
            (loads[j] = i) /\
            exists(k in NODES)(x[i, k] = j) /\
            exists(k in NODES)(x[i, j] = k)
        )
    );

% Depot Handling
constraint
    forall(i in COURIERS)(
        if exists(j in ITEMS)(loads[j] = i) then (
            exists(k in ITEMS)(x[i, n + 1] = k) /\
            exists(k in ITEMS)(x[i, k] = n + 1)
        ) else
            forall(k in NODES)(x[i, k] = k)
        endif
    );

% Subcircuit
constraint
    forall(i in COURIERS) (
        subcircuit([x[i, j] | j in NODES])
    );

% Symmetry Breaking
constraint
    forall(i in 1..m-1, z in i+1..m where l[i] == l[z]) (
        lex_less([x[i, k] | k in NODES], [x[z, k] | k in NODES]) /\
        lex_less([loads[j] = i | j in ITEMS], [loads[j] = z | j in ITEMS])
    );

% Define traveled_max_dist
constraint
    traveled_max_dist = max(y);

% Search Strategy
solve
    :: restart_luby(50)
    :: int_search(loads, first_fail, indomain_min)
    :: int_search(x, dom_w_deg, indomain_median)
    minimize traveled_max_dist;

% Output
output [
    "Total distance: ", show(traveled_max_dist), "\n",
    "Distances per courier: ", show(y), "\n",
    "Assignment of items to couriers: ", show(loads), "\n",
    "Routes per courier: ", show(x), "\n"
];
