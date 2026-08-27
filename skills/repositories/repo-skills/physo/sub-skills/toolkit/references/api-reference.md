# Toolkit API reference

This reference records the public names and signatures verified from the PhySO
1.2.0 source and installed package. It is intentionally focused on operating
routes, not every implementation helper.

## Convenience toolkit functions

### `physo.toolkit.get_library`

```python
get_library(
    X_names=["x1", "x2"], X_units=None,
    y_name="y", y_units=None,
    fixed_consts=[1.], fixed_consts_units=None,
    free_consts_names=["c0", "c1"], free_consts_units=None,
    free_consts_init_val=None,
    spe_free_consts_names=None, spe_free_consts_units=None,
    spe_free_consts_init_val=None,
    op_names=default_op_names, use_protected_ops=True,
    n_realizations=1, device="cpu", warn_about_units=False,
)
```

It returns `physo.physym.library.Library`. The convenience function converts
aligned value arrays into the low-level token configuration. In particular,
pass `free_consts_init_val=[1., 2.]` for two named constants; do not assume the
low-level name-to-value dictionary documented by `tokenize.make_tokens` is
accepted by this convenience wrapper.

`op_names` can be a list such as `['mul', 'add', 'sub', 'div', 'inv', 'n2',
'sqrt', 'neg', 'exp', 'log', 'sin', 'cos']`. The selected protected/unprotected
operation dictionary must contain every requested name. `n_realizations`
controls the shape and broadcast rules for spe constants.

### `get_expressions` and `get_prior`

```python
get_expressions(
    batch_size, max_length, library,
    candidate_wrapper=None, n_realizations=1,
)
get_prior(priors_config, max_length, expressions, library)
```

`get_expressions` returns an empty `VectPrograms`. Append or set valid integer
indices on it. `candidate_wrapper`, when supplied, is a callable taking a
candidate program function and `X`, then returning the wrapped prediction;
keep it differentiable when free constants are optimized. `get_prior`
validates the prior list and returns a prior collection for the supplied
batch. When calling `get_prior` directly, make
`max_length >= HardLengthPrior['max_length']`.

### `sample_random_expressions`

```python
sample_random_expressions(
    batch_size=1000, max_length=None,
    length_soft_loc=None, length_soft_scale=5.,
    X_names=["x1", "x2"], X_units=None,
    y_name="y", y_units=None,
    fixed_consts=[1.], fixed_consts_units=None,
    free_consts_names=["c0", "c1"], free_consts_units=None,
    free_consts_init_val=None,
    spe_free_consts_names=None, spe_free_consts_units=None,
    spe_free_consts_init_val=None,
    op_names=default_op_names, use_protected_ops=True,
    n_realizations=1, device="cpu", priors_config=None,
    verbose=True, warn_about_units=False,
)
```

It returns a `VectPrograms` batch. With no custom prior list, `max_length` is
the hard length and `length_soft_loc` can replace the default soft-length
prior. With `priors_config`, a `HardLengthPrior` entry is required and its
`max_length` is used; a list without that entry raises `ValueError`.

## Libraries and encoding

### `Library`

```python
Library(
    custom_tokens=None, args_make_tokens=None,
    superparent_units=None, superparent_name="y",
)
```

Use `get_library` for ordinary user workflows. Use the constructor directly
when supplying public `Token` objects or the `args_make_tokens` dictionary
accepted by `physo.physym.tokenize.make_tokens`.

Useful public attributes include `tokens`, `choosable_tokens`, `names`,
`choosable_names`, `name_to_idx`, `name_to_token`, `arity`, `var_type`,
`var_id`, `n_choices`, `n_library`, `n_input_var`, `n_class_free_const`,
`n_spe_free_const`, `class_free_constants_names`,
`spe_free_constants_names`, `free_constants_tokens`, `superparent_idx`,
`dummy_idx`, `invalid_idx`, `vocab_size`, and `terminal_units_provided`.

```python
library.encode(expressions_str, one_hot=False)
library.decode(expressions_idx, n_realizations=1)
library.get_choosable_prop(attr)
library.check_and_pad_spe_free_const_init_val(n_realizations)
library.reset_library()
```

`encode` accepts a batch-shaped list of inner string lists and only accepts
choosable token names. It returns a list of integer lists, or a list of
`(length, n_choices)` one-hot NumPy arrays. `decode` accepts a batch-shaped
list of inner lists containing Python `int` values. It pads different lengths
with the library's invalid placeholder and returns a `VectPrograms` object.
The input prefixes still need complete, arity-consistent trees.

### Tokens

The public token family is in `physo.physym.token`:

- `Token(name, sympy_repr, arity, complexity=1., var_type=0, function=None,
  init_val=np.nan, var_id=None, fixed_const=np.nan, ...)` is the validating
  base class.
- `TokenOp(name, sympy_repr, arity, complexity=1., function=None, ...)` is a
  callable operation.
- `TokenInputVar(name, sympy_repr, complexity=1., var_id=None, ...)` is a
  zero-arity data variable.
- `TokenFixedConst(name, sympy_repr, complexity=1., fixed_const=np.nan, ...)`
  is a fixed numeric terminal.
- `TokenClassFreeConst(..., complexity=1., init_val=np.nan, var_id=None, ...)`
  is shared across realizations.
- `TokenSpeFreeConst(..., complexity=1., init_val=np.nan, var_id=None, ...)`
  has one value per realization.
- `TokenSpecial(name, sympy_repr, arity, complexity=1., function=None, ...)`
  is for special placeholders.

Operations need a callable whose argument count equals `arity`; variables and
constants must have arity zero. Names and SymPy representations are shorter
than the package token limit. Units constraints, when present, are seven- or
fewer-dimensional float vectors.

## Data and expression batches

### `Dataset`

```python
Dataset(multi_X, multi_y, multi_y_weights=1., library=None)
```

`multi_X` and `multi_y` are lists of equal length. Each `X` is
`(n_dim, n_samples)` and each `y` is `(n_samples,)`; all realizations must
share `n_dim`, but sample counts may differ. `multi_y_weights` may be one
scalar, one scalar per realization, or one float vector per realization.

Useful attributes are `n_realizations`, `n_dim`, `n_samples_per_dataset`,
`n_all_samples`, `multi_X`, `multi_y`, `multi_y_weights`, flattened variants,
`detected_n_realizations`, and `detected_device`. Use `dataset.to(device)` to
move all stored tensors. The module also exposes `inspect_Xy`,
`inspect_multi_y_weights`, `flatten_multi_data`, and `unflatten_multi_data`.

### `VectPrograms`

```python
VectPrograms(
    batch_size, max_time_step, library,
    candidate_wrapper=None, n_realizations=None,
)
```

Primary construction methods:

```python
batch.append(new_tokens_idx, forbid_inconsistent_units=False,
             allow_invalid_placeholder=False)
batch.set_programs(tokens_idx, forbid_inconsistent_units=False,
                   allow_invalid_placeholder=False)
batch.get_prog(prog_idx=0, skeleton=False, detach=False)
batch.get_prog_tokens(prog_idx=0)
batch.get_programs_array(detach=False)
batch.status()
batch.get_parent(coords)
batch.get_children(coords)
batch.get_siblings(coords)
batch.get_ancestors(coords)
batch.get_parent_idx(coords, no_parent_idx_filler=None)
batch.get_sibling_idx(coords, no_sibling_idx_filler=None)
batch.get_ancestors_idx(coords, no_ancestor_idx_filler=None)
```

`new_tokens_idx` is a NumPy integer vector of shape `(batch_size,)` and
contains choosable token indices. `set_programs` appends one time step at a
time. `batch.tokens` contains vectorized arities, units, positions, depths,
and relationship masks. `batch.n_lengths`, `n_dummies`, `n_completed`,
`n_complexity`, `n_free_const_occurrences`, and `is_complete` are useful
status checks.

The batch also has `get_infix_str`, `get_infix_sympy`, `get_infix_pretty`,
`get_infix_latex`, `get_infix_fig`, `get_infix_image`, `show_infix`,
`get_tree_graph`, `get_tree_latex`, `get_tree_image`,
`get_tree_image_via_tex`, and `show_tree`; all take `prog_idx=0` first.
Graph/image methods have optional external dependencies; use plain text first.
`batch.batch_optimize_constants(X, y_target, free_const_opti_args=None,
 y_weights=1., i_realization=0, n_samples_per_dataset=None, mask=None,
n_cpus=1, parallel_mode=False)` is the CPU-safe sequential batch optimizer.

### `Program` and `Cursor`

```python
Program(
    tokens, library, free_consts=None, is_physical=None,
    candidate_wrapper=None, n_realizations=1, has_free_consts=None,
)
Cursor(programs, prog_idx=0, pos=0)
```

Prefer `batch.get_prog()` so the free-constant table is wired correctly. A
direct `Program` token list must be a complete tree:
`len(tokens) - sum(token.arity) == 1`.

`Program` routes are:

```python
program(X, i_realization=0, n_samples_per_dataset=None)
program.execute(X, i_realization=0, n_samples_per_dataset=None)
program.execute_wo_wrapper(X, i_realization=0, n_samples_per_dataset=None)
program.optimize_constants(
    X, y_target, y_weights=1., i_realization=0,
    n_samples_per_dataset=None, args_opti=None,
    freeze_class_free_consts=False,
)
program.get_infix_str()
program.get_sympy_local_dicts(replace_nan_with=1.)
program.get_infix_sympy(do_simplify=False, evaluate_consts=False,
                        replace_nan_with=1.)
program.get_infix_pretty(do_simplify=False)
program.get_infix_latex(replace_dummy_symbol=True, new_dummy_symbol="?",
                        do_simplify=True)
program.save(path)
program.detach()
```

`Cursor.token`, `token_prop(attr)`, `set_pos`, `child(i_child=0)`,
`parent`, and `sibling(i_sibling=0)` support focused tree navigation. The
`parent` and `sibling` interfaces are properties in this version, while
`child` is called as a method.

## Free constants and optimization

### `FreeConstantsTable`

```python
FreeConstantsTable(batch_size, library, n_realizations=1)
```

It owns `class_values` with shape `(batch_size, n_class_free_const)` and
`spe_values` with shape `(batch_size, n_spe_free_const, n_realizations)`, plus
`is_opti`, `opti_steps`, `shape`, `n_free_const_tokens`, and
`n_free_const_values`. Use `reset_class_values`, `reset_spe_values`,
`get_const_of_prog`, `flatten_like_data`, `df`, `detach`, `to`, and `cpu`.

### Low-level optimizer

```python
MSE_loss(func, params, y_target, y_weights=1.)
LBFGS_optimizer(params, f, n_steps=10, tol=1e-6, lbfgs_func_args={})
optimize_free_const(func, params, y_target, y_weights=1., loss="MSE",
                    method="LBFGS", method_args=None)
```

`params` is a list of differentiable tensors or one tensor. `func(params)`
must preserve the PyTorch computation graph. The returned history is a NumPy
array. `Program.optimize_constants` is the preferred wrapper because it
updates the table's optimization flags.

## Monitoring and result loading

```python
monitoring.RunLogger(save_path=None, do_save=False)
monitoring.RunVisualiser(
    epoch_refresh_rate=10, epoch_refresh_rate_prints=1,
    save_path=None, do_show=True, do_prints=True,
    do_save=False, draw_all_progs_fit=True,
)
monitoring.save_pareto_pkl(pareto_progs, fpath)
monitoring.read_pareto_pkl(fpath)
monitoring.RunLogger.get_pareto_front()
monitoring.RunVisualiser.visualise(run_logger, batch)
physo.read_pareto_pkl(fpath)
physo.read_pareto_csv(pareto_csv_path, sympy_X_symbols_dict=None,
                      return_df=False)
physo.load_expr(fpath)
```

`RunLogger.get_pareto_front()` returns complexity, program, reward, and RMSE
arrays. `RunVisualiser` can save curve/Pareto data, figures, and pickles when
`do_save=True`; `do_show=False` and `do_save=False` are safe for headless
inspection. `read_pareto_csv` parses the generated `expression` column and
inserts stored class-free-constant values; it is explicitly not suitable for
realization-specific spe constants. Use the PKL route for those programs.
`load_expr` loads one pickled `Program`, whereas `read_pareto_pkl` loads a
pickled Pareto list. Keep paths tied to the run's working directory and check
that the file exists before loading.
