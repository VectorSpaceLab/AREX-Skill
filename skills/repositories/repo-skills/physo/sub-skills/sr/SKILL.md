---
name: sr
description: "Single-dataset symbolic regression with PhySO SR, including units,
  weights, presets, logging, and Pareto inspection."
read_when: "Use when the user has one X/y dataset and wants physo.SR guidance,
  dimensional-analysis units, y_weights, candidate_wrapper, config0/config0b,
  CPU/parallel notes, logs, or a safe quick-start smoke."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# PhySO SR Sub-skill

## Role

Use this sub-skill to help a Researcher run **single-dataset symbolic regression** with `physo.SR`. It covers preparing one `X, y` dataset, optional point weights, dimensional-analysis units, free/fixed constants, operator choices, light run configurations, logging, and result/Pareto-front inspection. For root routing across all PhySO sub-skills, see the parent skill at [`../../SKILL.md`](../../SKILL.md).

## Boundaries

Included:
- One dataset with `X` shaped `(n_dim, n_samples)` and `y` shaped `(n_samples,)`.
- `X_names`, `X_units`, `y_name`, `y_units`, fixed constants, and SR free constants.
- `y_weights` as either one scalar or one per-sample vector aligned with `y`.
- `candidate_wrapper`, `op_names`, `use_protected_ops`, `config0`/`config0b` selection, `epochs`, `stop_reward`, `max_n_evaluations`, logging, and CPU-safe execution.
- Handoff to Pareto/log inspection helpers after a run.

Excluded:
- Multi-dataset `physo.ClassSR`, class free constants, and realization-specific free constants; use sibling [`class-sr`](../class-sr/SKILL.md) when the user has multiple datasets or class/spe constants.
- Benchmark-problem definitions or maintainer benchmark runners; use sibling [`benchmarks`](../benchmarks/SKILL.md) for packaged Feynman/Class benchmark loaders.
- Low-level expression/library construction and random-expression sampling; use sibling [`toolkit`](../toolkit/SKILL.md) for those APIs.
- Generic PyTorch or scikit-learn regression advice outside the PhySO SR workflow.

## Verified entry points

- `physo.SR(X, y, y_weights=1.0, X_names=None, X_units=None, y_name=None, y_units=None, fixed_consts=None, fixed_consts_units=None, free_consts_names=None, free_consts_units=None, free_consts_init_val=None, op_names=None, use_protected_ops=True, stop_reward=1.0, max_n_evaluations=None, stop_after_n_epochs=10, epochs=None, candidate_wrapper=None, run_config=None, get_run_logger=None, get_run_visualiser=None, parallel_mode=True, n_cpus=None, device="cpu")`
- `physo.config.config0.config0` and `physo.config.config0b.config0b` for light SR presets.
- `physo.learn.monitoring.RunLogger` and `physo.learn.monitoring.RunVisualiser` for logs and optional plots.
- `logs.get_pareto_front()` from the returned logger.
- `physo.read_pareto_pkl`, `physo.read_pareto_csv`, and `physo.load_expr` for saved-result inspection.

## Operating workflow

1. **Route first.** Stay here for one `X, y` dataset. If the request mentions several realizations, shared formula across datasets, class constants, or per-dataset constants, route to `class-sr`.
2. **Prepare numeric inputs.** Convert tabular data to floating arrays, then transpose feature matrices so `X.shape == (n_dim, n_samples)` and `y.shape == (n_samples,)`. Keep `y_weights` either a scalar or a per-sample float array with the same shape as `y`.
3. **Define units and constants.** If dimensional analysis matters, give every variable and constant a consistent units vector of length up to seven; otherwise omit units or use zero vectors. SR free constants are single-dataset/class-style constants only.
4. **Choose operators and wrappers.** Start with the default operator set unless the task needs a narrow grammar. Keep `candidate_wrapper` callable, top-level if multiprocessing is used, differentiable, and implemented with torch operations when free constants are optimized.
5. **Choose a preset.** Use `config0` for demos and short smokes. Use `config0b` when a quick SR task has free constants and you want more LBFGS constant-optimization steps without moving to heavier presets. Deep-copy presets before editing.
6. **Run safely.** For notebooks, debugging, and the verified CPU smoke path, set `parallel_mode=False`, `n_cpus=1`, and `device="cpu"`. This skill does not verify CUDA behavior.
7. **Inspect results.** Treat the returned `expression` as the current best `Program`; use `logs.get_pareto_front()` for the complexity/reward/RMSE front, and saved Pareto pkl/csv helpers for later inspection.
8. **Recover from failures.** Use [`references/troubleshooting.md`](references/troubleshooting.md) before changing algorithms; most SR failures are shape, units, weights, wrapper, preset-mutation, or optional-display issues.

## Input and output contract

Inputs expected by this sub-skill:
- `X`: float NumPy array or torch tensor convertible to shape `(n_dim, n_samples)`.
- `y`: float vector convertible to shape `(n_samples,)` with no NaNs.
- Optional `y_weights`: scalar, or float vector with the same sample length as `y`.
- Optional units: `X_units` length equals `n_dim`; `y_units`, `fixed_consts_units`, and `free_consts_units` use the same convention and vector length up to seven.
- Optional grammar/config: `op_names`, `use_protected_ops`, a deep-copied `run_config`, and a torch-compatible `candidate_wrapper`.

Outputs returned by `physo.SR`:
- `expression`: a `physo.physym.program.Program` for the best expression found so far.
- `logs`: a `RunLogger` with histories and `get_pareto_front()` returning `(complexities, programs, rewards, rmse)`.
- Optional saved artifacts if the logger/visualiser are configured to save: run CSV logs, Pareto CSV, Pareto pkl, and plots.

## Bundled references and helper

- [`references/workflows.md`](references/workflows.md): quick-start, weighted data, dimensional-analysis, wrapper, and result-inspection recipes.
- [`references/configurations.md`](references/configurations.md): preset choice, safe edits, stopping criteria, parallel/device notes, and operator/prior alignment.
- [`references/troubleshooting.md`](references/troubleshooting.md): recover from import, shape, unit, weight, wrapper, parallel, display, and Pareto-loading mistakes.
- [`scripts/smoke_sr_quick_start.py`](scripts/smoke_sr_quick_start.py): short CPU-only smoke adapted from the SR quick start; it runs a tiny weighted single-dataset SR call and reloads the Pareto pkl it writes.

## Related native tests and examples

Native candidates for later verification of this route:

- `physo.task.tests.sr_UnitTest`: deterministic `physo.SR` calls, including the canonical energy-style quick-start and a reduced-operator case that tolerates prior warnings.
- `physo.physym.tests.execute_UnitTest`: lower-level expression execution on CPU/CUDA-capable hosts; use only as execution evidence here, not as CUDA proof.
- `physo.physym.tests.program_display_UnitTest`: string, SymPy, LaTeX, and optional tree-display behavior; display extras can fail gracefully.
- `physo.learn.tests.monitoring_UnitTest`: SR logging, Pareto-front collection, and cleanup behavior.

Source examples distilled into this sub-skill:

- The bundled smoke helper adapts the canonical SR quick-start into a tiny CPU-only installed-package check.
- The y-weights demo material is distilled into the weighted-data workflow reference rather than copied as a runnable notebook.
- The damped harmonic oscillator demo is useful as a longer, dimensioned SR reference, but its long run settings are not bundled as a smoke helper.
- Feynman benchmark runners and job-file generators are maintainer/reference material, not SR runtime helpers; use benchmark-focused siblings for packaged benchmark problem loaders.
