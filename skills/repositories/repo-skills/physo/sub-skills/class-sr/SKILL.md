---
name: class-sr
description: "Multi-dataset class symbolic regression with shared and
  realization-specific free constants."
read_when: "Use when multiple related realizations must share one symbolic law
  with class and realization-specific constants."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Class SR

## Role
Use this sub-skill when the user has multiple realizations of the same phenomenon and wants one shared symbolic form with:
- class free constants shared by every realization
- realization-specific free constants (`spe_free_consts`)
- ClassSR-specific data-shape validation and quick-start guidance

If the user has only one dataset, route to the sibling `sr` sub-skill instead.
If the user mainly needs expression-tree or constant-table manipulation, hand off to the sibling `toolkit` sub-skill.

## Included
- `physo.ClassSR`
- `multi_X`, `multi_y`, `multi_y_weights`
- `class_free_consts_*` and `spe_free_consts_*`
- ClassSR config selection (`config0b`, `config1b`, `config2b`)
- safe quick-start execution on CPU
- loading and inspecting Pareto logs
- constant inspection handoff to toolkit-style workflows

## Excluded
- single-dataset `physo.SR`
- benchmark equivalence utilities and benchmark runner automation
- generated jobfile helpers and maintainer-only benchmark orchestration
- generic multi-task ML workflows that are not ClassSR

## Verified entry points
- `physo.ClassSR`
- `physo.config.config0b.config0b`
- `physo.config.config1b.config1b`
- `physo.config.config2b.config2b`
- `physo.read_pareto_pkl`
- `physo.load_expr`
- `run_logger.get_pareto_front()`
- `best_expr.free_consts.class_values`
- `best_expr.free_consts.spe_values`
- `best_expr.get_infix_sympy(evaluate_consts=True)`

## Canonical workflow
1. Build `multi_X` and `multi_y` as lists with one element per realization.
   - Each `X_i` must have shape `(n_dim, n_samples_i)`.
   - Each `y_i` must have shape `(n_samples_i,)`.
   - Different realizations may have different sample counts.
2. Provide weights with `multi_y_weights` when you need to bias one realization or one region of a realization.
3. Define constants and units.
   - `class_free_consts_*` are shared across realizations.
   - `spe_free_consts_*` may vary by realization.
4. Pick a ClassSR config.
   - `config0b`: quick smoke / demos
   - `config1b`: dimensional-analysis-heavy ClassSR and Milky Way streams
   - `config2b`: class benchmark style runs
   - prefer the `b` variants for ClassSR because they give more free-constant optimization steps
5. Run `physo.ClassSR(...)` on CPU for a smoke test, or on the target device if the environment is already verified.
6. Inspect the result with `best_expr.get_infix_pretty()`, `run_logger.get_pareto_front()`, and `best_expr.free_consts`.
7. If you need deeper program or constant-table work, switch to the sibling `toolkit` sub-skill instead of expanding this one.

## Input / output contract
- Input `multi_X`: list-like of length `n_realizations`; each item is array-like with shape `(n_dim, n_samples_i)`.
- Input `multi_y`: list-like of length `n_realizations`; each item is array-like with shape `(n_samples_i,)`.
- Input `multi_y_weights`: one of
  - a single scalar, broadcast to every realization
  - a list/array of length `n_realizations` containing one scalar per realization
  - a list/array of length `n_realizations` containing one weight array per realization with shape `(n_samples_i,)`
- Input `class_free_consts_names` / `class_free_consts_units` / `class_free_consts_init_val`: same length, one entry per shared constant.
  - In the `ClassSR` wrapper, pass init values in name order as a list/array-like container.
- Input `spe_free_consts_names` / `spe_free_consts_units` / `spe_free_consts_init_val`: same length, one entry per realization-specific constant.
  - In the `ClassSR` wrapper, pass init values in name order as a list/array-like container.
  - `spe_free_consts_init_val` may use a scalar or a length-`n_realizations` vector per constant.
- Output `best_expression`: `physo.physym.program.Program`
- Output `run_logger`: logger object with Pareto-front access
- Output `best_expression.free_consts.class_values`: shape `(1, n_class_free_consts)`
- Output `best_expression.free_consts.spe_values`: shape `(1, n_spe_free_consts, n_realizations)`
- Output `best_expression.get_infix_sympy(evaluate_consts=True)`: array with one expression per realization

## Quick safe run
Use the bundled smoke helper for a CPU-safe sanity check:

```bash
python skills/disco/physo/sub-skills/class-sr/scripts/smoke_class_sr_quick_start.py
```

The helper uses tiny deterministic data, short epochs, CPU execution, and temporary log files.

## Troubleshooting
- If imports fail, check the environment first: `physo`, `torch`, `numpy`, `sympy`, `pandas`, `matplotlib`, `scikit-learn`.
- If a realization has a different sample count, that is allowed; only each `X_i` / `y_i` pair must match.
- If `multi_y_weights` length does not match `multi_y`, or any per-point weight array has the wrong length, fix the list shape first.
- If class/spe constant unit arrays do not match the name counts, fix the name/unit lists before running.
- If `spe_free_consts_init_val` is a vector, its length must match `n_realizations`.
- If `parallel_mode` or CUDA behavior is unclear, keep the smoke run on `device='cpu'` with `parallel_mode=False`.
- CUDA-capable torch builds may still print parallel-mode warnings during a CPU smoke run; treat them as expected noise unless the run actually fails.
- If LaTeX or display extras are missing, prefer `get_infix_pretty()` or `get_infix_sympy()`; pretty LaTeX rendering is optional.
- If you need saved logs or Pareto reloads, use `run_logger.get_pareto_front()` first and then `physo.read_pareto_pkl(...)` on the saved `_pareto.pkl` file.

## Related native tests and examples
- `physo/task/tests/class_sr_UnitTest.py` — canonical ClassSR task check
- `physo/physym/tests/free_const_UnitTest.py` — class/spe constant table behavior
- `physo/physym/tests/dataset_UnitTest.py` — realization and weight-shape validation
- `physo/benchmark/ClassDataset/tests/ClassProblem_UnitTest.py` — benchmark-shaped multi-dataset loading
- `demos/class_sr_quick_start.py` — source quick-start recipe adapted by the smoke script
- `demos/class_sr/demo_free_fall/demo_free_fall.py` — reference ClassSR example with class and spe constants
- `demos/class_sr/demo_milky_way_streams/MW_streams_run.py` — reference-only, longer benchmark-style run

## See also
- Root `physo` skill for package-level routing and shared troubleshooting
- Sibling `toolkit` skill for program inspection, constant-table work, and log loading
- Sibling `benchmarks` skill for benchmark problem loaders and symbolic comparison
