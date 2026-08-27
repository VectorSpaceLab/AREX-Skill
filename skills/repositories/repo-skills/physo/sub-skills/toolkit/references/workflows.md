# Toolkit workflows

The examples below are intentionally small and CPU-safe. They use no network
and do not require notebook execution or plotting.

## 1. Build a library, encode, decode, and inspect

A library's `choosable_names` is the authoritative vocabulary. Prefix order is
operator first, followed by its operands:

```python
import numpy as np
from physo.toolkit import get_library

library = get_library(
    X_names=["x"],
    y_name="y",
    fixed_consts=[1.0],
    free_consts_names=["c"],
    free_consts_init_val=[1.0],
    op_names=["add", "mul"],
    warn_about_units=False,
)

prefix = [["mul", "c", "x"], ["add", "x", "x"]]
assert set(prefix[0]).issubset(set(library.choosable_names))
encoded = library.encode(prefix)
# Convert explicitly if an upstream model returned NumPy integer scalars.
encoded_for_decode = [[int(token_idx) for token_idx in row] for row in encoded]
programs = library.decode(encoded_for_decode)

print(programs.status())
print(programs.get_infix_str(0))       # (c*x)
print(programs.get_prog(0).get_infix_sympy())
```

`encode` returns a list of integer lists, not a rectangular array. Different
prefix lengths are allowed. `encode(..., one_hot=True)` returns one matrix per
expression with trailing dimension `library.n_choices`; it is a model-facing
representation and should not be passed to `decode` without first recovering
integer indices.

An expected validation path is:

```python
try:
    library.encode([["mul", "missing", "x"]])
except ValueError as exc:
    print(exc)  # Token name 'missing' is not in the library.
```

Placeholders are not a user expression vocabulary. `decode` internally pads
shorter programs with its invalid placeholder; it does not make an invalid
operator arity valid.

## 2. Sample random expressions under bounded priors

```python
import numpy as np
import torch
from physo.toolkit import sample_random_expressions

np.random.seed(7)
torch.manual_seed(7)
programs = sample_random_expressions(
    batch_size=2,
    max_length=5,
    X_names=["x"],
    y_name="y",
    fixed_consts=[1.0],
    free_consts_names=["c"],
    free_consts_init_val=[1.0],
    op_names=["mul", "add", "sub", "div", "inv", "n2", "sqrt",
              "neg", "exp", "log", "sin", "cos"],
    verbose=False,
    warn_about_units=False,
    device="cpu",
)
print(programs.status())
print(programs.n_lengths, programs.is_complete)
```

For a custom prior list, make the hard length explicit and do not rely on a
conflicting top-level `max_length`:

```python
priors_config = [
    ("HardLengthPrior", {"min_length": 3, "max_length": 5}),
    ("SoftLengthPrior", {"length_loc": 4, "scale": 1.5}),
]
programs = sample_random_expressions(
    batch_size=2, max_length=None, priors_config=priors_config,
    X_names=["x"], y_name="y", fixed_consts=[1.0],
    free_consts_names=[], op_names=["add", "mul"],
    verbose=False, warn_about_units=False,
)
```

When `priors_config` is present, `sample_random_expressions` requires a
`HardLengthPrior`, takes that entry's `max_length`, and ignores the separate
`max_length`/`length_soft_loc` override. A direct `get_prior` call instead
requires its `max_length` argument to be at least the hard-prior maximum.

## 3. Create an empty batch and append/set programs

Use `get_expressions` when an upstream model supplies integer choices one step
at a time:

```python
from physo.toolkit import get_expressions

batch = get_expressions(batch_size=1, max_length=3, library=library)
indices = np.asarray(library.encode([["mul", "c", "x"]])[0], dtype=int)
batch.set_programs(indices[None, :])
program = batch.get_prog(0, detach=True)
```

For `append`, each call takes a NumPy integer vector of shape
`(batch_size,)`, not a Python scalar. Use `batch.lib("arity")`,
`batch.lib_names`, and `batch.status()` when debugging a model's token
choices.
`allow_invalid_placeholder=True` is for controlled padded inputs, not for
silently repairing a malformed expression.

## 4. Validate data with `Dataset`

```python
import torch
from physo.physym.dataset import Dataset

X = torch.tensor([[0., 1., 2., 3.]], dtype=torch.float64)
y = 2.5 * X[0]
data = Dataset([X], [y], multi_y_weights=1.0, library=library)
assert data.n_dim == 1
assert data.n_samples_per_dataset.tolist() == [4]
assert data.multi_X_flatten.shape == (1, 4)
```

For multiple realizations, use `multi_X=[X0, X1]` and `multi_y=[y0, y1]`.
Each realization may have a different sample count but all `X` tensors must
have the same first dimension. A weight vector must have the same sample count
as its matching `y`; a scalar weight is broadcast.

## 5. Execute and fit one free constant

```python
import torch
from physo.toolkit import get_library

fit_library = get_library(
    X_names=["x"], y_name="y", fixed_consts=[],
    free_consts_names=["a"], free_consts_init_val=[1.0],
    op_names=["mul"], warn_about_units=False,
)
fit_program = fit_library.decode(
    [fit_library.encode([["mul", "a", "x"]])[0]]
).get_prog(0)
X = torch.linspace(0., 1., 8, dtype=torch.float64).unsqueeze(0)
y_target = 2.5 * X[0]
history = fit_program.optimize_constants(X=X, y_target=y_target)
assert len(history) > 0
print(fit_program.free_consts.class_values)
print(torch.mean((fit_program(X) - y_target) ** 2))
```

The default is MSE with the package's LBFGS settings. An advanced call can
supply the low-level options through `args_opti`, for example
`{"loss": "MSE", "method": "LBFGS", "method_args": {"n_steps": 8,
"tol": 1e-10, "lbfgs_func_args": {"max_iter": 4,
"line_search_fn": "strong_wolfe"}}}`. The target, weights, and execution
output must have matching shapes and compatible floating dtypes.

If the program has no free-constant token, optimization intentionally returns
an empty history and records zero steps. That is a successful no-op, not an
optimizer failure.

## 6. Use autograd or a candidate wrapper

`Program` execution is PyTorch-backed, so ordinary autograd works as long as
all operations remain differentiable:

```python
X_grad = X.clone().detach().requires_grad_(True)
y_pred = fit_program(X_grad)
dy_dX = torch.autograd.grad(
    outputs=y_pred,
    inputs=X_grad,
    grad_outputs=torch.ones_like(y_pred),
    create_graph=True,
)[0]
```

For expression-layer wrapping, pass a callable when creating the batch:

```python
def square_wrapper(func, X):
    return func(X) ** 2

wrapped_batch = get_expressions(
    batch_size=1, max_length=3, library=library,
    candidate_wrapper=square_wrapper,
)
```

The wrapper receives the candidate function and `X`. Keep it in PyTorch if you
will optimize constants; converting to NumPy, detaching, or using
non-differentiable control paths breaks gradient-based fitting. For full
`physo.SR`/`physo.ClassSR` wrapper arguments, route to the SR/Class SR sibling
skills.

## 7. Class and realization-specific constants

Class constants are shared; spe constants vary by realization. Create a
library with `n_realizations=2` and a spe initializer like `[1.0]` (broadcast)
or `[1.0, 1.2]` (explicit):

```python
multi_library = get_library(
    X_names=["x"], y_name="y", fixed_consts=[],
    free_consts_names=["c"], free_consts_init_val=[1.0],
    spe_free_consts_names=["k"], spe_free_consts_init_val=[1.0],
    op_names=["add", "mul"], n_realizations=2,
    warn_about_units=False,
)
programs = multi_library.decode(
    [multi_library.encode([["add", "mul", "k", "x", "c"]])[0]],
    n_realizations=2,
)
program = programs.get_prog(0)
print(program.free_consts.class_values.shape)  # (1, 1)
print(program.free_consts.spe_values.shape)    # (1, 1, 2)
```

For a flattened multi-realization execution, concatenate `X0` and `X1` in
that order and call `program.execute(X_flat,
n_samples_per_dataset=np.array([len0, len1]))`. The same counts must be used
for target/weights during `optimize_constants`. Use
`FreeConstantsTable.flatten_like_data` when preparing custom low-level
execution code.

## 8. Inspect a tree without rendering it

```python
from physo.physym import program as program_module

batch = library.decode([[int(i) for i in library.encode(
    [["mul", "c", "x"]])[0]]])
print(batch.tokens.arity[0])
print(batch.tokens.depth[0])
print(batch.status())

cursor = program_module.Cursor(batch, prog_idx=0, pos=0)
print(cursor.token)
print(cursor.child(0).token)
```

For vectorized relationships, use the coordinates recorded in
`batch.tokens.parent_pos`, `children_pos`, `siblings_pos`, and
`ancestors_pos`, or call `get_parent`, `get_children`, and `get_ancestors`.
The first token is position zero in prefix order. `Program.get_infix_str`,
`get_infix_pretty`, and `get_infix_sympy` are the preferred display/debug
surface when graph dependencies are unavailable.

## 9. Load monitoring and Pareto results

A run configured with `RunLogger`/`RunVisualiser` can expose a Pareto front:

```python
complexity, programs, reward, rmse = logs.get_pareto_front()
best = programs[-1]
print(best.get_infix_pretty())
print(best.get_infix_sympy(evaluate_consts=True))
print(best.free_consts.df())
```

For files created by the visualizer:

```python
import physo

pareto_programs = physo.read_pareto_pkl("run_curves_pareto.pkl")
best_program = pareto_programs[-1]

# CSV is for non-spe fronts and returns evaluated SymPy expressions.
expressions, pareto_df = physo.read_pareto_csv(
    "run_curves_pareto.csv", return_df=True
)

# A single Program pickle uses the separate loader.
program = physo.load_expr("one_program.pkl")
```

Resolve paths relative to the process working directory, or pass an absolute
path that exists. PKL preserves `Program` objects and is the reliable route for
spe constants. CSV reconstruction uses stored class constants and does not
support realization-specific constant columns.

## 10. Optional representations

- `Program.get_infix_str()` is plain text and has no renderer dependency.
- `get_infix_sympy()` and `get_infix_pretty()` use SymPy and are suitable for
  logs and terminal inspection.
- `get_infix_latex()` returns a LaTeX string; it does not itself require the
  system `latex` executable.
- `get_infix_fig()`/`show_infix()` involve Matplotlib and may use system
  LaTeX.
- `VectPrograms.get_tree_graph()` requires `pygraphviz`.
- `get_tree_latex()` additionally requires `dot2tex`.
- `get_tree_image_via_tex()` additionally depends on `pdflatex` and
  `pdf2image`; `get_tree_image()` needs graph rendering and Pillow.

Probe optional display calls and keep a plain-text fallback. Never make a
successful expression round-trip depend on an image or PDF.
