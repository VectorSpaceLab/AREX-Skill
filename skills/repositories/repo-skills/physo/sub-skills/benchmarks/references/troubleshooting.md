# Benchmark troubleshooting

## Invalid equation selector

- Feynman accepts the normalized range `0..119`; Class accepts `0..7`.
- Equation names are exact strings from `EQS_FEYNMAN_DF["Name"]` or
  `EQS_CLASS_DF["Name"]`, including punctuation and spaces.
- A positive out-of-range index or missing name commonly ends as
  `IndexError: single positional indexer is out-of-bounds` because the loader
  selects a pandas row with `.iloc`.
- A negative index is not safely rejected: `.iloc[-1]` can select the final
  equation. Reject negative values before calling the constructor.
- If `i_eq` and `eq_name` are both supplied, the current implementation uses
  `i_eq`. Pass one selector after validating it.

A safe caller-side pattern is:

```python
def checked_feynman(index):
    if not isinstance(index, (int, np.integer)) or not 0 <= int(index) < Feyn.N_EQS:
        raise ValueError(f"Feynman index must be in [0, {Feyn.N_EQS})")
    return Feyn.FeynmanProblem(i_eq=int(index))
```

Use the analogous `Cls.N_EQS` check for Class. Names should be checked against
the corresponding table before constructing the problem.

## Sample shape mismatches

Keep the axes explicit:

| Problem | Input to target | Generated output |
| --- | --- | --- |
| Feynman | `X: (n_vars, n_samples)` | `y: (n_samples,)` |
| Class, one realization | `X: (n_vars, n_samples)`, `K: (n_spe,)` | `y: (n_samples,)` |
| Class, generated batch | `multi_X: (n_realizations, n_vars, n_samples)` | `multi_y: (n_realizations, n_samples)` |
| Class with constants | same as above | `K: (n_realizations, n_spe)` |

Typical mistakes are passing `(n_samples, n_vars)`, passing all `multi_X` to
`target_function` instead of one realization, or passing a whole `K` matrix
instead of `K[i]`. Inspect `pb.n_vars`, `pb.n_spe`, and every `.shape` before
calling the target. Use `return_K=True` if later symbolic binding or target
re-evaluation needs the sampled Class constants.

The generators use NumPy's global random state. Set `np.random.seed` before a
small diagnostic when reproducibility matters; do not infer sample equality
without controlling that seed.

## Symbolic assumptions and parsing

`FeynmanProblem` and `ClassProblem` construct SymPy symbols with `real=True`
and range-derived positive/negative assumptions. A freshly created
`sympy.Symbol("x0")` is not necessarily the same symbolic object for
simplification purposes even though it prints the same way.

- Use `pb.sympy_X_symbols_dict` for normalized `x*` names.
- With `original_var_names=True`, use
  `pb.sympy_original_to_X_symbols_dict` for source variable names.
- For a Class candidate, use `pb.get_sympy(K_vals=...)` to bind every `k*`
  symbol before comparing a realization.
- Use `formula_sympy` for assumption-aware structure and
  `formula_sympy_eval` when fixed constants should be numerical.
- Do not parse `formula_latex`; it is display text.

If parsing creates unexpected functions or unresolved symbols, print
`expr.free_symbols` and compare it with `pb.sympy_X_symbols_dict` (and the
Class `K` dictionary when appropriate). Also confirm the candidate uses the
problem's normalized or original names consistently.

## Comparison and trigonometry

`compare_expression` may return `True` for a zero difference, a finite constant
difference, or a finite constant ratio. That is the shipped benchmark rule, not
a strict identity or residual threshold. A report with
`symbolic_error_is_constant=True` deserves an explicit explanation and, when
needed, a numerical check on generated data.

For trigonometric candidates:

- Keep `pi` symbolic while parsing exact phase identities, rather than using
  `pb.local_dict`, which maps `pi` to numeric `numpy.pi`.
- `handle_trigo=True` only rationalizes nearby numeric values as bounded
  fractions of `pi`; it is not a universal trig simplifier.
- `round_decimal` affects float rounding and the trig tolerance. A candidate
  can pass at `round_decimal=1` after a small offset rounds to zero and fail at
  `round_decimal=3`.
- `prevent_zero_frac=True` and `prevent_inf_equivalence=True` are safety
  defaults. Preserve them unless the caller has a documented reason to change
  them.

Always retain the full report, including `sympy_exception`, and state whether
the vanilla or trigonometric path established the result.

## Plotting and display dependencies

The benchmark problem modules import Matplotlib at module import time, so a
missing `matplotlib` is an installation/runtime-dependency failure rather than
an ordinary `show_sample` fallback. Install the normal PhySO scientific
runtime dependencies and verify `import physo.benchmark...` before proceeding.

`show_sample` itself is optional for data/equivalence workflows. In a headless
environment:

```python
pb.show_sample(n_samples=8, do_show=False, save_path="sample.png")
```

Set a non-interactive Matplotlib backend before importing pyplot when the host
requires it (for example, `MPLBACKEND=Agg`). Missing system LaTeX produces an
expected import-time warning from PhySO's display code; it does not mean the
loader or symbolic comparison failed. Avoid requiring LaTeX, `dot2tex`,
`pygraphviz`, or image-conversion extras for this sub-skill.

## Do not launch the maintainer benchmark

`benchmarking/readme_reproducibility.md` documents CLI runners, result
analysis, and HPC jobfile generation for the paper/maintainer experiments.
That document is a boundary reference, not a request to reproduce the runs.

Do **not** invoke these as part of a normal Researcher task:

- `benchmarking/FeynmanBenchmark/feynman_run.py`
- `benchmarking/ClassBenchmark/classbench_run.py`
- `benchmarking/*_make_run_file.py`
- the associated results-analysis scripts or generated result folders

They train, write run directories/plots/CSVs, or submit many jobs. Stop after a
small loader/equivalence check and route a deliberate reproduction request to
a separately approved benchmark experiment workflow. The bundled smoke helper
is intentionally limited to a few in-memory samples.

## Native diagnosis

Use the CPU-safe package tests when a loader behavior itself is in doubt:

```bash
python -m unittest physo.benchmark.FeynmanDataset.tests.FeynmanProblem_UnitTest -q
python -m unittest physo.benchmark.ClassDataset.tests.ClassProblem_UnitTest -q
```

These exercise all shipped loader rows with small generation counts. They do
not validate long SR runs, CUDA behavior, or maintainer benchmark results.
