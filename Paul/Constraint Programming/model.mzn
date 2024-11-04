include "globals.mzn";
% Parameters
int: m;                          % number of courriers
int: n;                          % number of distribution points
array[1..m] of int: l;           % vehicle capacities
array[1..n] of int: s;           % demand of each distribution point
array[1..n+1, 1..n+1] of int: D; % distance matrix (n+1 corresponds to the origin)

% Decision variables
array[1..m, 1..n+1] of var 1..n+1: x; % x[i, j1] = j2 if courier i goes from j1 to j2, j1 otherwise

int: sum_of_row_max = sum([ max([D[i, j] | j in 1..n+1]) | i in 1..n+1 ]);

array[1..m] of var 0..sum_of_row_max: y; % y[i] is the total distance travelled by courier i
var 0..sum_of_row_max: traveled_max_dist;

% Objective: Minimize the total travel distance
constraint
    forall(i in 1..m) (
        y[i] = sum([ D[j1, x[i, j1]] | j1 in 1..n+1 where x[i, j1] != j1])
    );
constraint
    traveled_max_dist = max(y);

% Constraints
%If the courier left an must return to the deposit, if it doesn't travel x[i,k] = k
constraint
    forall(i in 1..m)(
        if x[i, n+1] != n+1 then count([x[i, j1] | j1 in 1..n], n+1, 1) 
        else forall(k in 1..n) (x[i, k] = k) endif
    );


%constraint
%    forall(i in 1..m)(
%        (x[i, n+1] != n+1) -> count([x[i, j1] | j1 in 1..n], n+1) = 1
%    );

constraint
    forall(i in 1..m)(
        sum([s[j1] | j1 in 1..n where x[i, j1] != j1]) <= l[i]   %capacity constraint
    );

constraint
    forall(j in 1..n) (
        sum([x[i, j] != j | i in 1..m]) == 1  %exactly one courier per package
    );

%if two couriers have the same load, we make sure they cannot have the paths reversed between them.
constraint
    forall(i in 1..m-1, z in i+1..m where l[i] == l[z]) (
        lex_less([x[i,k] | k in 1..n+1] , [x[z,k] | k in 1..n+1])
    );

constraint
    forall(i, j in 1..m where i < j /\ l[i] >= l[j]) (
        (exists(k in 1..n) (x[i, k] != k) /\ exists(k in 1..n) (x[j, k] != k)) -> 
        sum([s[k] | k in 1..n where x[i, k] != k]) >= sum([s[k] | k in 1..n where x[j, k] != k])
    );

constraint
    forall(i in 1..m)(
        subcircuit([x[i, j] | j in 1..n+1])  % Use the subcircuit global constraint for each courier's route
    );
% Solve the model
%solve :: int_search(x, first_fail, indomain_min) minimize traveled_max_dist; %original search
%solve :: int_search(x, occurrence, indomain_min) minimize traveled_max_dist; % optimize the variables with highest number of constrants first


output [
  "totaldistance: ", show(traveled_max_dist), "\n",
  "Assignment: ", show(x), "\n"
];