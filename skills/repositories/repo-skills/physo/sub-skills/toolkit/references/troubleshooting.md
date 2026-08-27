# Toolkit troubleshooting

## Unknown token names

`Library.encode` checks every name against `library.choosable_name_to_idx` and
raises `ValueError` for a missing name. Inspect `library.choosable_names` and
copy the exact spelling. Fixed constants created by `get_library` are named
from their rounded numeric value, so `1.0` is commonly a library name rather
than `1`. Operations must also match the selected protected/unprotected
operation dictionary. Do not guess indices across libraries: indices are
library-local.

A token not in the library is the difficult-case diagnostic for this route:
try encoding it, capture the exact name in the exception, then rebuild the
library with the desired operation/constant/variable rather than editing an
index by hand.

## Wrong token arity or incomplete prefix

Prefix tokens consume operands according to `token.arity`: a binary token such
as `add` needs two following subtrees and a unary token such as `neg` needs one.
A complete tree satisfies:

```text
number of tokens - sum(token.arity) == 1
```

`Library.decode` pads different-length batch rows but does not repair a bad
prefix. Inspect `library.arity`, `batch.status()`, `batch.n_lengths`, and
`batch.is_complete`. A malformed `set_programs`/`append` input can fail while
placing a token or while completing dummies; return to readable prefix names
and rebuild the row.

## Encode/decode shape and dtype mismatch

- `encode` requires an outer list/array of expressions and an inner list/array
  of strings. Calling `encode(expr)` for one inner expression instead of
  `encode([expr])` is invalid.
- `decode` requires the outer batch and each inner row to be a list/array of
  Python `int` values. Convert `np.int64` values with `int(value)` if the
  strict source assertion rejects them.
- One-hot arrays from `encode(..., one_hot=True)` are not integer prefixes.
  Recover the argmax indices before decoding.
- Empty batches or empty expression rows do not provide a maximum decode length;
  reject them before calling `decode`.
- A decoded batch pads rows with the library invalid placeholder. Compare
  `batch.status()` or `batch.n_lengths` instead of treating padded columns as
  real operators.

## `HardLengthPrior` and `max_length`

When `sample_random_expressions` receives `priors_config`, it searches for a
`HardLengthPrior`, requires one, and uses that entry's `max_length`; the
separate `max_length` and `length_soft_loc` arguments do not override it. A
custom list without `HardLengthPrior` raises:

```text
ValueError: No HardLengthPrior found in priors_config ...
```

Keep the values consistent in user-facing code. For direct
`get_prior(priors_config, max_length, expressions, library)`, use a
`max_length` at least as large as the hard prior's maximum or the argument
checker raises an assertion. Also ensure the hard minimum is attainable with
the selected arities and vocabulary; priors that zero every choice cannot
sample a program.

## Invalid library or operator setup

Check the following before constructing `Library`:

1. `len(X_names)` equals the number of input rows, and names are unique enough
   for SymPy/display use.
2. Units rows align with variables/constants and are float vectors with no
   more than seven entries. `y_units` is one-dimensional.
3. Fixed, class-free, and spe-free names, units, and initial-value arrays have
   matching first dimensions. Toolkit convenience APIs expect aligned arrays;
   low-level `tokenize.make_tokens` accepts name-keyed dictionaries.
4. Every `op_names` value exists in the selected operation dictionary. Unknown
   names raise `functions.UnknownFunction` during tokenization.
5. Custom operation tokens have a callable with the declared arity. Variable,
   free-constant, and fixed-constant tokens have arity zero and the matching
   `var_type`/`var_id` contract.
6. A library with terminal units omitted is still usable without physical-unit
   priors, but `terminal_units_provided` is false and a warning is expected.

For custom tokens, use the public typed constructors in
`physo.physym.token`, then pass them as `Library(custom_tokens=[...])`. Do not
rely on private fields or mutate token arrays without `reset_library()`.

## Free-constant initializer and optimizer shapes

Class constants are common to all realizations:

```text
class_values: (batch_size, n_class_free_const)
```

Spe constants vary by realization:

```text
spe_values: (batch_size, n_spe_free_const, n_realizations)
```

A spe initializer scalar is broadcast by
`check_and_pad_spe_free_const_init_val`; an initializer vector must have
exactly `n_realizations` values. A wrong vector length raises an assertion.
Use `program.free_consts.df()` to inspect names and flattened columns.

For one dataset, `X`, `y_target`, and `y_weights` must have compatible sample
lengths. For flattened realizations, concatenate in the same order as
`n_samples_per_dataset`, and pass that exact integer array to both execution
and optimization. `Dataset` can validate the per-realization shapes before
creating a `Program`. Keep all tensors on the same CPU device in the verified
baseline and avoid integer targets.

The optimizer is gradient-based. A custom `candidate_wrapper` or low-level
`func(params)` must preserve differentiability; converting predictions to
NumPy or detaching constants inside the function prevents LBFGS from finding
a gradient. If no free-constant token occurs in a program, an empty history
and zero optimization steps are intentional.

## Display and tree rendering dependencies

Importing PhySO may warn that system `latex` is unavailable. That warning is
expected in the CPU baseline. Use these fallbacks in order:

1. `get_infix_str()` for deterministic plain text.
2. `get_infix_sympy()` or `get_infix_pretty()` for symbolic/terminal output.
3. `get_infix_latex()` for a LaTeX string without invoking a renderer.
4. Figures or trees only when their optional tools are installed.

`get_tree_graph` needs `pygraphviz`; `get_tree_latex` needs `dot2tex` as well;
`get_tree_image_via_tex` needs `pdflatex` and `pdf2image`; image routes also
need Pillow and a working Graphviz installation. The source methods may print
an inability message or return `None` for missing optional imports, and later
calls may fail if a `None` graph is used. Check the result and retain the
plain-text fallback. Do not install or invoke these tools merely to validate
encoding or optimization.

The synthetic display case is: request a tree/LaTeX rendering on a host with
no system `latex`. The correct result is a warning/fallback to text or SymPy,
not a claim that tree image generation was verified.

## Monitoring, Pareto, and result paths

`RunLogger(save_path=..., do_save=True)` and `RunVisualiser(save_path=...,
do_save=True)` derive output paths from the chosen save path. Confirm the
current working directory and the exact suffix before loading:

- `physo.read_pareto_pkl(path)` loads a list of detached `Program` objects.
- `physo.read_pareto_csv(path, return_df=True)` loads the CSV and parsed SymPy
  expressions for non-spe fronts.
- `physo.load_expr(path)` loads one pickled `Program`.

CSV loading is reference-only for realization-specific spe constants; use the
PKL front for Class SR programs. If a logger has no positive-reward candidate,
`get_pareto_front()` has no valid front to return; inspect rewards and the run
log before indexing `[-1]`. If a pickle cannot load, verify that the file is
complete and that the installed PhySO version can import the serialized class.
Do not treat a missing path as a symbolic-expression failure.

## CPU/backend boundary and routing

The verified toolkit route is CPU-only. `device="cpu"` and
`parallel_mode=False` are the safe defaults for examples and checks. No CUDA
behavior is claimed here. For a full SR/Class SR run, send the request to the
corresponding sibling skill; for benchmark problem definitions or selectors,
send it to the benchmarks sibling. This sub-skill only handles the expression
and result-inspection layer those workflows may hand off.
