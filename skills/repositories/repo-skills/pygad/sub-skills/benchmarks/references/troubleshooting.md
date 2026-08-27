# PyGAD benchmark troubleshooting

Use this guide when a benchmark callable, quality indicator, or benchmark-based
GA run fails. Most issues come from sign confusion, wrong genome shape, or the
wrong indicator/reference-front format.

## Fast triage checklist

1. Is the benchmark output in PyGAD maximization format already?
2. Does the chromosome length match `problem.num_genes`?
3. For multi-objective runs, is the fitness function returning a vector, not a
   scalar?
4. For TSP, are `gene_space`, `gene_type`, and `allow_duplicate_genes=False`
   all set together?
5. For hypervolume, is the reference point strictly worse than every solution on
   every objective?
6. For DTLZ, did you choose `num_objectives >= 2` and a matching `num_genes`?

## Benchmark-class errors

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| `num_objectives must be at least 2 for the DTLZ suite` | DTLZ was instantiated with `num_objectives=1`. | Use at least two objectives or choose a single-objective benchmark. |
| `Pass exactly one of coordinates or distance_matrix.` | TSP constructor received both inputs or neither. | Provide only one of the two inputs. |
| `coordinates must be a 2D array` | TSP coordinates are not shaped as `(num_cities, 2)` or similar. | Reshape the coordinates to a 2D array with at least two rows. |
| `distance_matrix must be square` | TSP distance matrix has mismatched dimensions. | Supply a square matrix with the same number of rows and columns. |
| `distance_matrix entries must be non-negative` | TSP matrix contains negative distances. | Fix the matrix; TSP expects non-negative distances. |
| `weights and values must have the same length` | Knapsack input arrays are mismatched. | Make the item lists the same length. |
| `weights must be non-negative` / `values must be non-negative` | Knapsack data contains negative entries. | Sanitize the item arrays before constructing the benchmark. |
| `capacity must be positive` | Knapsack capacity is zero or negative. | Pass a positive capacity. |

## Multi-objective and indicator errors

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| `single-objective ... parent selection type ... only works for multi-objective` | An NSGA selector was used with a scalar fitness function. | Return a vector fitness or switch to a single-objective selector. |
| `fitness must be a 2D array` | A quality indicator received a 1D or scalar input. | Pass the full front matrix with shape `(num_solutions, num_objectives)`. |
| `reference_point must have shape (...)` | Hypervolume reference point has the wrong length. | Pass one value per objective. |
| `reference_point must be smaller than every solution on every objective` | The hypervolume reference point is not strictly worse than the front. | Shift the reference point further down in every objective. |
| IGD/GD values look correct but the front is inverted | The front was supplied in minimization form. | Negate it once before scoring, or use the benchmark callable directly. |
| `spacing` returns `0.0` | Only one point was supplied, or all nearest-neighbor distances are equal. | This is expected for one point; otherwise inspect the front spread. |

## ZDT-specific issues

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| ZDT fitness looks "double negated" | The benchmark already returns `[-f1, -f2]`. | Do not negate the returned values again. |
| `ZDT3` has no `pareto_front()` helper | That helper is not bundled in the current release. | Build a reference set analytically or use another ZDT family. |
| ZDT values seem clipped | The benchmark class clips solutions into the supported domain. | Keep the GA bounds aligned with the problem bounds. |

## DTLZ-specific issues

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| The objective vector is the wrong length | `num_genes` does not match `num_objectives + num_distance_vars - 1`. | Recompute the chromosome length from the DTLZ formula. |
| A Pareto check does not land on the expected sphere or hyperplane | The distance variables are not at their optimal value. | For DTLZ2/3/4 use distance variables near `0.5`; for DTLZ1 the front sum is `0.5`. |
| NSGA-III warns about too small a population | `sol_per_pop` is smaller than the reference-point count. | Increase the population or lower `nsga3_num_divisions`. |

## Knapsack-specific issues

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| The GA returns mostly overweight solutions | The genome is not binary or the benchmark was not used as the fitness function. | Set `fitness_func=problem`, `gene_space=[0, 1]`, and `gene_type=int`. |
| Feasible solutions are not preserved | The population does not contain a known feasible baseline, or retention is too low. | Seed a feasible solution in `initial_population` and use elitism for smoke checks. |

## TSP-specific issues

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| Best fitness is a very large negative number | The chromosome is not a valid permutation. | Set `allow_duplicate_genes=False` and use `gene_space=list(range(num_cities))`. |
| Tour length and fitness seem reversed | TSP fitness is negative tour length by design. | Report `-fitness` when you want the actual distance. |
| Duplicate or missing cities slip into the population | The permutation constraints are incomplete. | Use the problem-provided `gene_space`, `gene_type`, and `allow_duplicate_genes`. |

## Indicator interpretation notes

- Hypervolume is larger-is-better.
- IGD and GD are smaller-is-better.
- Spacing is smaller-is-better.
- Dominated rows are removed inside the hypervolume calculation, so dominated
  points usually do not change the score.

## Safe recovery pattern

When a benchmark smoke run fails, rebuild the case from the benchmark object
itself:

1. Recreate the benchmark with the smallest known valid parameters.
2. Call the benchmark directly on a hand-built solution.
3. Check the sign and length of the returned fitness.
4. Only then wire the benchmark into `pygad.GA` and the indicators.
