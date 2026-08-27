---
name: benchmarks
description: "Load PhySO's shipped Feynman and Class benchmark problems,
  generate bounded samples, inspect symbolic metadata, and compare candidate
  SymPy expressions."
read_when: "Use when a task needs benchmark-problem data or symbolic-equivalence
  checks; do not use it to launch the maintainer benchmark suites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PhySO benchmark problems

## Role

This sub-skill is the bounded, read-only benchmark-data route for the installed
`physo` package. It teaches a Researcher to select a Feynman or Class problem,
inspect its target and metadata, generate a small in-memory sample, obtain the
prefix form, and apply the package's symbolic comparison convention.

It is not a general benchmarking or model-training skill. Keep generated arrays
small unless the caller explicitly owns a separate experiment workflow.

## Boundaries

**Included**

- `FeynmanProblem` for the 120 Feynman entries (bulk indices 0--99 and bonus
  indices 100--119), including equation-name lookup.
- `ClassProblem` for the 8 Class entries, including realization-specific `K`
  constants and equation-name lookup.
- Formula, variable, target, range, unit, SymPy-assumption, and prefix metadata.
- `generate_data_points`, `target_function`, `get_sympy`, and non-blocking
  `show_sample` usage.
- `FeynmanProblem.compare_expression` and
  `physo.benchmark.utils.symbolic_utils.compare_expression`.
- The small loader check in `scripts/smoke_benchmark_loaders.py`.

**Excluded**

- Running SR or Class SR (`physo.SR` and `physo.ClassSR`); route those requests
  to [`sr`](../sr/SKILL.md) or [`class-sr`](../class-sr/SKILL.md).
- Full benchmark reproduction, noisy benchmark campaigns, result analysis,
  cluster/HPC jobfiles, and long-running runners.
- Generic data-science benchmark design or numerical-only model scoring.
- Pareto-front and training-log handling; route those questions to
  [`toolkit`](../toolkit/SKILL.md) or the root skill.

The maintainer scripts `benchmarking/FeynmanBenchmark/feynman_run.py` and
`benchmarking/ClassBenchmark/classbench_run.py` are reference-only. The
`benchmarking/*_make_run_file.py` files and `benchmarking/utils.py` jobfile
helper are deliberately outside this runtime skill.

## Verified entry points

The following imports and package facts are verified for PhySO 1.2.0:

```python
import physo.benchmark.FeynmanDataset.FeynmanProblem as Feyn
import physo.benchmark.ClassDataset.ClassProblem as Cls
from physo.benchmark.utils import symbolic_utils as su

feyn_pb = Feyn.FeynmanProblem(i_eq=0)
class_pb = Cls.ClassProblem(i_eq=0)
```

The verified inspection/runtime baseline is CPU-only Python 3.12 with NumPy,
SymPy, pandas, Matplotlib, scikit-learn, and a CPU PyTorch build. No CUDA claim
is made here. Import-time warnings about unavailable system LaTeX are expected
and do not by themselves invalidate loading or comparison.

## Workflow

1. **Validate the selector before constructing the object.** Use an integer in
   `0 <= i_eq < Feyn.N_EQS` (120) or `0 <= i_eq < Cls.N_EQS` (8), or use the
   exact `eq_name` from the dataset. A name can be inspected with
   `Feyn.EQS_FEYNMAN_DF["Name"]` or `Cls.EQS_CLASS_DF["Name"]`. If both selector
   arguments are supplied, the current constructors take the index branch.
2. **Load and inspect metadata.** Start with `print(pb)`, then inspect
   `formula_sympy`, `formula_sympy_eval`, `formula_latex`, `X_names`,
   `X_lows`, `X_highs`, `X_units`, `y_name`, and `y_units`. Class problems also
   expose `K_names`, `K_lows`, `K_highs`, and `K_units`; `K` means one row of
   realization-specific constants, not a Class SR class constant.
3. **Generate a bounded sample.** Set `np.random.seed(...)` when reproducible
   values matter and pass an explicit small `n_samples`. Feynman returns
   `X.shape == (pb.n_vars, n_samples)` and `y.shape == (n_samples,)`. Class
   returns `multi_X.shape == (n_realizations, pb.n_vars, n_samples)` and
   `multi_y.shape == (n_realizations, n_samples)`; with `return_K=True`, it
   also returns `K.shape == (n_realizations, pb.n_spe)`.
4. **Check the target directly.** For Feynman use `pb.target_function(X)`.
   For a Class realization use `pb.target_function(multi_X[i], K[i])`. Compare
   shapes before calling `np.allclose`; do not transpose the package's
   `(variables, samples)` convention.
5. **Inspect the expression representation.**
   `pb.get_prefix_expression()` returns a dictionary with `tokens_str`,
   `arities`, and `tokens`, traversed in SymPy pre-order. For a Class problem,
   the prefix form still contains symbolic `k*` tokens. Use
   `pb.get_sympy(K_vals=...)` to substitute one or more concrete `K` rows.
6. **Compare symbolically.** Parse a candidate with the problem's assumption-
   carrying symbol dictionary, then call the problem wrapper for Feynman or
   `su.compare_expression` for Class. Follow the exact examples in
   [symbolic-equivalence.md](references/symbolic-equivalence.md), and retain
   the returned `report` instead of relying only on the Boolean.
7. **Stop at inspection.** If the request asks for all equations, noise sweeps,
   SR training, job submission, or result reproduction, hand off to the
   appropriate root/SR/Class SR workflow and keep this route as the loader and
   equivalence utility only.

## Input/output contracts

| Operation | Inputs | Outputs and invariants |
| --- | --- | --- |
| `FeynmanProblem(i_eq=...)` or `eq_name=...` | Valid index or exact name | One problem; `X` is variables-first; target `y` is one-dimensional. |
| `ClassProblem(i_eq=...)` or `eq_name=...` | Valid index or exact name | One problem; `K` has one row per realization and one column per `K_names`. |
| `generate_data_points` | Small positive `n_samples`; Class also `n_realizations` | NumPy float arrays sampled within declared input and constant ranges. |
| `target_function` | Feynman `X`, or Class `X` plus one `K` row | Target values for the supplied shape; it does not validate a transposed data layout for you. |
| `get_prefix_expression` | No arguments | Dict keys `tokens_str`, `arities`, `tokens` with equal lengths. |
| `compare_expression` | SymPy expressions with matching assumption-aware symbols | `(is_equivalent: bool, report: dict)`; report includes symbolic error/fraction and solution flags. |

## Safe helper and native checks

Run the bundled helper from an environment where `physo` is installed:

```bash
python skills/disco/physo/sub-skills/benchmarks/scripts/smoke_benchmark_loaders.py
```

It loads Feynman problem 0 and Class problem 0, generates only a few points,
checks target evaluation and array shapes, and prints stable metadata. It never
runs a benchmark trainer or creates result directories.

The corresponding native candidates are:

- `python -m unittest physo.benchmark.FeynmanDataset.tests.FeynmanProblem_UnitTest -q`
- `python -m unittest physo.benchmark.ClassDataset.tests.ClassProblem_UnitTest -q`

These tests iterate over all shipped equations with small samples; they are
CPU-safe correctness checks, not full SR benchmark reproduction.

## Troubleshooting

See [problem-loaders.md](references/problem-loaders.md) for selector, shape,
metadata, and plotting details; [symbolic-equivalence.md](references/symbolic-equivalence.md)
for assumptions, rounding, and trigonometric comparison; and
[troubleshooting.md](references/troubleshooting.md) for recovery and the
maintainer-runner boundary.

Common first responses:

- Normalize an index before construction. Positive out-of-range and unknown
  names currently surface as pandas `IndexError`; negative `.iloc` indices can
  accidentally select the last row, so reject them in caller code.
- Use the exact shape contracts above. Feynman is `(n_vars, n_samples)`, not
  `(n_samples, n_vars)`; Class adds a realization axis.
- Parse candidates with `pb.sympy_X_symbols_dict` (or the documented original-
  name dictionary), not fresh symbols with different assumptions.
- Treat `compare_expression` as the benchmark's symbolic convention, not as a
  numerical error metric. Inspect its report, especially when rounding or
  trigonometric handling is enabled.
- Use `show_sample(..., do_show=False)` in headless work. Missing Matplotlib is
  an installation problem because these benchmark modules import it; missing
  system LaTeX only affects optional display and is normally warning-level.

## Related routes

- Root routing: [`../../SKILL.md`](../../SKILL.md)
- Single-dataset SR: [`../sr/SKILL.md`](../sr/SKILL.md)
- Class SR data-shape and training guidance: [`../class-sr/SKILL.md`](../class-sr/SKILL.md)
- Low-level expression and result inspection: [`../toolkit/SKILL.md`](../toolkit/SKILL.md)
