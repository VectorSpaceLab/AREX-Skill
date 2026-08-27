# Benchmark problem loaders

## Select a problem safely

The shipped data tables expose the authoritative counts:

```python
import physo.benchmark.FeynmanDataset.FeynmanProblem as Feyn
import physo.benchmark.ClassDataset.ClassProblem as Cls

assert 0 <= feynman_index < Feyn.N_EQS       # 120: 0--119
assert 0 <= class_index < Cls.N_EQS          # 8: 0--7
feynman_names = Feyn.EQS_FEYNMAN_DF["Name"].tolist()
class_names = Cls.EQS_CLASS_DF["Name"].tolist()
```

Construct by index or exact name:

```python
feyn_pb = Feyn.FeynmanProblem(i_eq=42)
feyn_by_name = Feyn.FeynmanProblem(eq_name="I.15.1")
class_pb = Cls.ClassProblem(i_eq=4)
class_by_name = Cls.ClassProblem(eq_name="Damped Harmonic Oscillator B")
```

The constructors use `if i_eq is not None` before the `eq_name` branch. If
both are passed, the index is used. Positive out-of-range indexes and unknown
names eventually raise `IndexError` from the underlying pandas selection. A
negative index is especially dangerous: pandas `.iloc[-1]` selects the last
row. Enforce the non-negative range in caller code rather than relying on the
constructor to reject it.

## Feynman metadata and data

A `FeynmanProblem` represents one of 100 bulk equations or 20 bonus equations.
Useful fields include:

- `i_eq`, `i_eq_feyn`, `eq_name`, `eq_filename`, and `SRBench_name` identify the
  selected row.
- `n_vars`, `X_names`, `X_names_original`, `X_lows`, `X_highs`, and `X_units`
  describe input variables. `X_units` has one five-component unit vector per
  variable, with shape `(n_vars, 5)`.
- `y_name`, `y_name_original`, and `y_units` describe the output. `y_units` has
  shape `(5,)`.
- `formula_original` is the CSV formula; `formula_sympy` contains SymPy symbols
  carrying range-derived assumptions; `formula_sympy_eval` additionally
  evaluates fixed constants such as `pi`; `formula_latex` is a display string.
- `X_sympy_symbols`, `sympy_X_symbols_dict`,
  `sympy_original_to_X_symbols_dict`, and `local_dict` provide parsing maps.

The default normalized naming is `x0`, `x1`, ... and `y`. Use
`original_var_names=True` only when the candidate text uses the source names;
the array order and shapes do not change. For normalized candidate parsing:

```python
candidate = sympy.parse_expr(
    "x0*exp(-x1)", local_dict=feyn_pb.sympy_X_symbols_dict
)
```

Generate deliberately bounded data. The implementation default is one million
samples, so do not use the default for a smoke or inspection:

```python
import numpy as np
np.random.seed(0)
X, y = feyn_pb.generate_data_points(n_samples=8)
assert X.shape == (feyn_pb.n_vars, 8)
assert y.shape == (8,)
assert np.allclose(y, feyn_pb.target_function(X))
```

`X` is variables-first. Each variable is sampled uniformly between its
`X_lows` and `X_highs`; `target_function` evaluates the formula and returns a
one-dimensional array for the trailing sample axis.

`show_sample(n_samples=100, do_show=True, save_path=None)` generates new data
and plots one panel per variable. In a headless environment use a small count,
`do_show=False`, and optionally a caller-owned output path. It is a plotting
convenience, not a benchmark runner.

## Class metadata and data

A `ClassProblem` represents one of eight Class SR equations. In addition to
normal input/output metadata, inspect:

- `n_vars` and `n_spe`: input-variable and realization-specific-constant counts.
- `X_names`, `X_names_original`, `X_lows`, `X_highs`, and `X_units`; Class unit
  vectors have seven components.
- `K_names`, `K_names_original`, `K_lows`, `K_highs`, and `K_units` for the
  realization-specific `K` constants.
- `formula_original`, `formula_sympy`, `formula_sympy_eval`, `formula_latex`,
  `sympy_X_symbols_dict`, `sympy_K_symbols_dict`, and `local_dict`.

With normalized names, input variables are `x0`, `x1`, ... and realization
constants are `k0`, `k1`, .... With `original_var_names=True`, source names are
used for display and parsing. Class problems can have zero or more `K`
constants; always use `pb.n_spe` and the metadata rather than assuming a fixed
count.

Generate a small set of realizations as follows:

```python
np.random.seed(0)
multi_X, multi_y, K = class_pb.generate_data_points(
    n_samples=8, n_realizations=3, return_K=True
)
assert multi_X.shape == (3, class_pb.n_vars, 8)
assert multi_y.shape == (3, 8)
assert K.shape == (3, class_pb.n_spe)
for i in range(3):
    assert np.allclose(multi_y[i], class_pb.target_function(multi_X[i], K[i]))
```

The `K` rows are sampled from `K_lows`/`K_highs` and are required to reproduce
the corresponding target realization. If `return_K=False`, the same method
returns only `(multi_X, multi_y)` and the sampled constants are not recoverable
from that call.

For a concrete expression, pass one row per requested realization to
`get_sympy`:

```python
exprs = class_pb.get_sympy(K_vals=K[:2])
assert exprs.shape == (2,)
```

When `K_vals=None`, the method samples random constants and returns one
expression. Use an explicit `K_vals` row for reproducible comparison. The
`target_function` contract is one realization at a time: `X.shape` is
`(n_vars, n_samples)` and `K.shape` is `(n_spe,)`.

## Prefix representation

Both problem types expose:

```python
prefix = pb.get_prefix_expression()
tokens = prefix["tokens_str"]
arities = prefix["arities"]
sympy_tokens = prefix["tokens"]
assert len(tokens) == len(arities) == len(sympy_tokens)
```

The helper delegates to `sympy_to_prefix` and walks the SymPy expression in
pre-order. `tokens_str` contains function names, symbols, or formatted numeric
constants; `arities` contains the number of child arguments for each token;
`tokens` contains the corresponding SymPy objects/classes. A Class prefix form
contains symbolic `k*` entries until a concrete expression is obtained with
`get_sympy`.

Do not treat this dict as a serialized PhySO program. It is a compact inspection
view; constructing a library/program from it belongs to the toolkit route.
