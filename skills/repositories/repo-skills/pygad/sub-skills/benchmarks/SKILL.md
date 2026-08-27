---
name: benchmarks
description: "Use PyGAD benchmark problem classes and quality indicators for
  classic, ZDT/DTLZ, knapsack, and TSP optimization workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# benchmarks

Use this sub-skill when the task is to work with the built-in benchmark
problem families under `pygad.benchmarks` or the quality indicators in
`pygad.utils.quality_indicators`.

## Route elsewhere

- Custom GA tuning, callbacks, persistence, or general optimization debugging:
  use the genetic-algorithm sub-skill.
- Plotting benchmark fronts, report generation, or headless figure handling:
  use the results-and-visuals sub-skill.

## What this sub-skill covers

- Classic continuous problems: Sphere, Rastrigin, Rosenbrock, Griewank,
  Schwefel, Ackley, and Himmelblau.
- Multi-objective test suites: ZDT1, ZDT2, ZDT3, ZDT4, ZDT6, DTLZ1, DTLZ2,
  DTLZ3, and DTLZ4.
- Combinatorial problems: 0/1 Knapsack and TSP.
- Quality indicators: hypervolume, inverted generational distance,
  generational distance, and spacing.

## Operating flow

1. **Pick the benchmark family.** Match the problem to the target shape:
   - classic single-objective minima,
   - ZDT trade-off fronts,
   - DTLZ many-objective fronts,
   - knapsack selection, or
   - TSP permutations.
2. **Match the genome to the benchmark attributes.**
   - Continuous benchmark classes expose `num_genes`, `num_objectives`, and
     `bounds`.
   - Knapsack exposes `gene_space=[0, 1]` and `gene_type=int`.
   - TSP exposes `gene_space=list(range(num_cities))`, `gene_type=int`, and
     `allow_duplicate_genes=False`.
3. **Remember PyGAD maximizes.** The benchmark callables already return values
   in maximization form, so do not negate them again.
4. **Choose a compatible GA setup.**
   - Continuous benchmarks usually pair with `init_range_low/high` from the
     benchmark `bounds` and real-coded operators such as SBX plus polynomial
     mutation.
   - ZDT and DTLZ runs should use NSGA-style parent selection.
   - Knapsack and TSP should use integer/permutation-aware gene settings.
5. **Evaluate quality indicators on the final front.** Use the final
   `ga.last_generation_fitness` matrix and, for ZDT, the bundled
   `pareto_front()` helper when available.
6. **Use the smoke script for a quick end-to-end check.** It runs compact
   Sphere, ZDT1, DTLZ2, Knapsack, and TSP examples and saves state only in
   temporary files.

## Reference map

- Public API signatures, default values, return contracts, and validation
  rules: [references/api-reference.md](references/api-reference.md)
- Recommended benchmark workflows and indicator recipes:
  [references/workflows.md](references/workflows.md)
- Common failures and fixes: [references/troubleshooting.md](references/troubleshooting.md)
- Deterministic bundled smoke script: [scripts/benchmark_smoke.py](scripts/benchmark_smoke.py)

## Validation signals

- Single-objective benchmark runs return a scalar fitness and
  `ga.best_solution(...)` should approach the known optimum.
- ZDT and DTLZ runs return vector fitness with
  `ga.last_generation_fitness.shape[1] == problem.num_objectives`.
- `problem.pareto_front()` is available for ZDT1, ZDT2, ZDT4, and ZDT6 and
  returns negated reference-front points in PyGAD maximization format.
- `hypervolume` requires a reference point that is smaller than every fitness
  vector entry.
- `spacing` returns `0.0` for fewer than two solutions.
