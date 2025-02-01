include "globals.mzn";
% Parameters
int: m;                          % number of couriers
int: n;                          % number of distribution points
array[1..m] of int: l;           % vehicle capacities
array[1..n] of int: s;           % demand of each distribution point
array[1..n+1, 1..n+1] of int: D; % distance matrix (n+1 corresponds to the origin)

% Decision variables
array[1..m, 1..n+1] of var 1..n+1: x; % x[i, j1] = j2 if courier i goes from j1 to j2, j1 otherwise
array[1..n] of var 1..m: bins;        % bins[j] indicates which courier handles item j

% Lower and Upper Bounds for traveled_max_dist
% Dynamically calculated bounds
int: obj_lowerbound = max(
    max(i in 1..n)(D[n+1, i] + D[i, n+1]),
    max(i in 1..n, j in 1..n where i != j)(D[i, j])
);
int: obj_upperbound = sum(i in 1..n)(
    max(j in 1..n+1)(D[i, j])
) ;
array[1..m] of var 0..obj_upperbound: y; % y[i] is the total distance travelled by courier i

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
% Link bins to x
constraint forall(j in 1..n)(
    exists(i in 1..m)(x[i, j] != j /\ bins[j] = i)
);
% Bin Packing Constraint for Load Capacity
constraint bin_packing_capa(l, bins, s);

   
%Exactly one courier per package
constraint forall(j in 1..n) (
    count([x[i, j] != j | i in 1..m], true) == 1
);

constraint
    forall(i in 1..m)(
        subcircuit([x[i, j] | j in 1..n+1])  % Ensure each courier's route forms a valid subcircuit
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



solve
:: restart_luby(n*m) 
:: int_search(x, dom_w_deg, indomain_split)   % Relax 50% of the decision variables

minimize traveled_max_dist;

output [
  "totaldistance: ", show(traveled_max_dist), "\n",
  "Assignment: ", show(x), "\n"
];
