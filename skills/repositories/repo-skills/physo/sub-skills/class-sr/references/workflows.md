# ClassSR workflows

## 1) Canonical quick-start flow

Use this when you need the shortest path from multiple realizations to a ClassSR run.

1. Prepare `multi_X` and `multi_y`.
   - `multi_X[i]` has shape `(n_dim, n_samples_i)`.
   - `multi_y[i]` has shape `(n_samples_i,)`.
   - The sample count may differ per realization.
2. Add `multi_y_weights` only if you need to bias a realization or a region inside one realization.
3. Declare shared constants and realization-specific constants.
4. Select a config.
   - `config0b` for a smoke or demo run
   - `config1b` for dimensional-analysis-heavy ClassSR or the Milky Way streams case
   - `config2b` for class-benchmark-style runs
5. Run `physo.ClassSR(...)`.
6. Inspect the Pareto front and recovered constants.

Typical pattern:

```python
best_expr, run_logger = physo.ClassSR(
    multi_X,
    multi_y,
    multi_y_weights=multi_y_weights,
    X_names=["x0"],
    X_units=[[0, 0, 0]],
    y_name="y",
    y_units=[0, 0, 0],
    fixed_consts=[1.0],
    fixed_consts_units=[[0, 0, 0]],
    class_free_consts_names=["c0"],
    class_free_consts_units=[[0, 0, 0]],
    spe_free_consts_names=["k0"],
    spe_free_consts_units=[[0, 0, 0]],
    run_config=physo.config.config0b.config0b,
    op_names=["add", "mul"],
    parallel_mode=False,
    epochs=2,
)

complexities, programs, rewards, rmses = run_logger.get_pareto_front()
print(best_expr.get_infix_pretty())
print(best_expr.free_consts.class_values)
print(best_expr.free_consts.spe_values)
```

## 2) CPU-safe smoke flow

Use the bundled helper when you only need to prove the API works end to end.

```bash
python skills/disco/physo/sub-skills/class-sr/scripts/smoke_class_sr_quick_start.py
```

The helper keeps the data tiny, uses deterministic inputs, runs on CPU, and cleans up its temporary logs.

## 3) Inspecting constants after a run

ClassSR splits constants into two groups:
- class free constants: shared by all realizations
- spe free constants: one value per realization

Useful checks:

```python
best_expr.free_consts.class_values.shape
best_expr.free_consts.spe_values.shape
best_expr.get_infix_sympy(evaluate_consts=True)
```

Interpretation tips:
- `class_values` should have one row per program and one column per shared constant.
- `spe_values` should have one row per program, one axis for realization-specific constants, and one axis for realizations.
- `get_infix_sympy(evaluate_consts=True)` returns one expression per realization because the spe constants differ by realization.

## 4) Reloading saved Pareto fronts

If the run logger saved a `_pareto.pkl` file, reload it with the public package helper:

```python
pareto_programs = physo.read_pareto_pkl("path/to/run_pareto.pkl")
```

This is the cleanest way to inspect a saved class-sr result without reopening the original run state.

## 5) Optional benchmark-shaped data source

If you want curated benchmark-shaped ClassSR data instead of synthetic toy data, use the benchmark loader as a source of realizations:

```python
from physo.benchmark.ClassDataset.ClassProblem import ClassProblem
pb = ClassProblem(i_eq=0, original_var_names=False)
multi_X, multi_y = pb.generate_data_points(n_samples=100, n_realizations=4)
```

Keep the benchmark loader in a reference role here; benchmark equivalence utilities and benchmark runners belong to the benchmarks skill, not this one.

## Config choice cheat sheet

| Config | Best for | Notes |
| --- | --- | --- |
| `config0b` | quick smoke and tutorials | lightest ClassSR preset |
| `config1b` | DA-heavy ClassSR and Milky Way streams | more aggressive search; good for units-aware cases |
| `config2b` | class benchmark style work | good general ClassSR preset |

For ClassSR, prefer the `b` variants because they leave more room for free-constant optimization during candidate evaluation.
