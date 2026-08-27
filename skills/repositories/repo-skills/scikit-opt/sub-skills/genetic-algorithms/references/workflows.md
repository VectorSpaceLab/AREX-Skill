# Workflows

## Choose the GA-family class

| Problem shape | Pick | Why |
| --- | --- | --- |
| Bounded search with Gray-coded or mixed discrete steps | `GA` | Supports `precision`, integer grids, and the standard binary GA workflow. |
| Same search, but you want elite preservation | `EGA` | Keeps the best `n_elitist` individuals through each generation. |
| Naturally continuous search | `RCGA` | Uses real-coded chromosomes and avoids bit decoding. |
| Permutation or routing problems | hand off to `routing-and-combinatorial` | This sub-skill only acknowledges `GA_TSP` as the route handoff. |

## Basic GA workflow

1. Define a scalar objective that accepts one candidate `x`.
2. Set `n_dim`, `lb`, `ub`, and `precision`.
3. Choose `size_pop` as an even integer.
4. Run once or in chunks.
5. Read `best_x`, `best_y`, and the history fields.

```python
from sko.GA import GA

ga = GA(
    func=objective,
    n_dim=3,
    size_pop=20,
    max_iter=10,
    lb=[-2, -2, -1],
    ub=[2, 2, 3],
    precision=[2, 1, 0.5],
)

best_x, best_y = ga.run()
```

## Continue a run

`run(max_iter)` continues from the current population instead of restarting from scratch. That means two calls accumulate history.

```python
best_x, best_y = ga.run(10)
best_x, best_y = ga.run(20)
```

Use this pattern when you want a short smoke first and a longer extension later. The same object keeps `generation_best_*` and `all_history_*` growing across calls, so `ga.run(10); ga.run(20)` means 30 total generations on one instance.

## Integer and mixed-precision search

- Set `precision` to integers for integer steps.
- Mix integers and floats in the same `precision` sequence when some variables are discrete and others are continuous.
- If the requested step grid does not align neatly with a power-of-two Gray-code lattice, the implementation may extend the upper bound internally so the encoding still works.
- If you need a fractional step such as `0.5` and the grid behaves awkwardly, rescale the variable first and optimize the scaled version.

A practical mixed example:

```python
GA(
    func=objective,
    n_dim=3,
    lb=[-2, -2, -1],
    ub=[2, 2, 3],
    precision=[2, 1, 0.5],
)
```

## When to choose elitism

Choose `EGA` when a tiny but strong elite carry-over is more important than maximum exploration. Keep `n_elitist` small relative to `size_pop`.

## Constraint handling

- Use `constraint_eq` for equations that should evaluate to zero.
- Use `constraint_ueq` for inequalities that should be less than or equal to zero.
- Remember that the implementation uses penalty terms, so feasible individuals are favored only after penalty adjustment.

If a constrained run looks overly punitive, tighten the bounds or repair candidates before optimization.

## History diagnostics

- `generation_best_Y` is the best value for each generation.
- `all_history_Y` is the full population objective history.
- `all_history_FitV` is the ranked fitness history.
- `generation_best_X` records the candidate that won each generation.

Use these fields for convergence plots, restart decisions, and regression checks.
