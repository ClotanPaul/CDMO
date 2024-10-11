% Parameters
int: m;                    % number of vehicles
int: n;                    % number of distribution points
array[1..m] of int: l;      % vehicle capacities
array[1..n] of int: s;      % demand of each distribution point
array[1..n+1, 1..n+1] of int: D;  % distance matrix (n+1 corresponds to the depot)

% Decision variables
array[1..m, 1..n] of var 0..1: x; % x[i,j] = 1 if vehicle i visits distribution point j

% Objective: Minimize the total travel distance
var int: total_distance = sum(i in 1..m, j in 1..n, k in 1..n+1)(x[i,j] * D[j,k]);

% Constraints
constraint forall(i in 1..m)(
  sum(j in 1..n)(x[i,j] * s[j]) <= l[i] % Vehicle capacity constraints
);

constraint forall(j in 1..n)(
  sum(i in 1..m)(x[i,j]) = 1 % Each distribution point must be visited by exactly one vehicle
);

constraint forall(i in 1..m)(
  sum(j in 1..n)(x[i,j]) > 0 % Each vehicle must visit at least one distribution point
);

% Solve the model
solve minimize total_distance;

output [
  "totaldistance: ", show(total_distance), "\n",
  "Assignment: ", show(x), "\n"
];
