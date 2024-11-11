include "globals.mzn";

% Parameters
int: m;                          % number of couriers
int: n;                          % number of distribution points
array[1..m] of int: l;           % vehicle capacities
array[1..n] of int: s;           % demand of each distribution point
array[1..n+1, 1..n+1] of int: D; % distance matrix (n+1 corresponds to the origin)

% Decision variables
array[1..m, 1..n+1] of var 1..n+1: x; % x[i, j1] = j2 if courier i goes from j1 to j2, j1 otherwise

int: sum_of_row_max = sum([ max([D[i, j] | j in 1..n+1]) | i in 1..n+1 ]);

array[1..m] of var 0..sum_of_row_max: y; % y[i] is the total distance travelled by courier i


% Lower and Upper Bounds for traveled_max_dist
int: obj_lowerbound = max(i in 1..n)(D[n+1, i] + D[i, n+1]);  % minimum round-trip distance to any point
array[1..n] of int: max_dists = [max(j in 1..n)(D[i, j]) | i in 1..n];
int: obj_upperbound = sum(i in 1..n)(max_dists[i]) + max(i in 1..n)(D[n+1, i]) + max(i in 1..n)(D[i, n+1]);

% Objective variable with bounds
var obj_lowerbound..obj_upperbound: traveled_max_dist;

% Objective: Minimize the maximum travel distance
constraint
    forall(i in 1..m) (
        y[i] = sum([ D[j1, x[i, j1]] | j1 in 1..n+1 where x[i, j1] != j1])
    );
constraint
    traveled_max_dist = max(y);

% Constraints
% If the courier left the depot, it must return to the depot. If it doesn't travel, x[i,k] = k
constraint
    forall(i in 1..m)(
        if x[i, n+1] != n+1 then count([x[i, j1] | j1 in 1..n], n+1, 1) 
        else forall(k in 1..n) (x[i, k] = k) endif
    );

constraint
    forall(i, j in 1..m where i < j /\ l[i] >= l[j]) (
        sum([s[k] | k in 1..n where x[i, k] != k]) >= sum([s[k] | k in 1..n where x[j, k] != k])
    );

constraint
    forall(i in 1..m)(
        sum([s[j1] | j1 in 1..n where x[i, j1] != j1]) <= l[i]   % Capacity constraint
    );

constraint
    forall(j in 1..n) (
        sum([x[i, j] != j | i in 1..m]) == 1  % Exactly one courier per package
    );

% If two couriers have the same load, we ensure their routes are lexicographically ordered to break symmetry.
constraint
    forall(i in 1..m-1, z in i+1..m where l[i] == l[z]) (
        lex_less([x[i, k] | k in 1..n+1], [x[z, k] | k in 1..n+1])
    );

constraint
    forall(i, j in 1..m where i < j /\ l[i] >= l[j]) (
        (exists(k in 1..n) (x[i, k] != k) /\ exists(k in 1..n) (x[j, k] != k)) -> 
        sum([s[k] | k in 1..n where x[i, k] != k]) >= sum([s[k] | k in 1..n where x[j, k] != k])
    );

constraint
    forall(i in 1..m)(
        subcircuit([x[i, j] | j in 1..n+1])  % Ensure each courier's route forms a valid subcircuit
    );

% Solve the model using the Luby restart strategy with the specified number of restarts
solve :: restart_luby(50) 
    :: int_search(x, dom_w_deg, indomain_median) minimize traveled_max_dist;

output [
  "totaldistance: ", show(traveled_max_dist), "\n",
  "Assignment: ", show(x), "\n"
];
