# Symbolic API reference

The examples below use the stable module paths:

```python
import torch
from neuromancer.constraint import variable, Variable, Constraint, Objective
from neuromancer.loss import PenaltyLoss, BarrierLoss, AugmentedLagrangeLoss
from neuromancer.system import Node
from neuromancer.problem import Problem
```

The package root exposes module attributes such as `neuromancer.constraint`,
`neuromancer.loss`, `neuromancer.problem`, and `neuromancer.system`. Treat
module-qualified imports as the portability contract instead of assuming every
class is directly available from `import neuromancer as nm`.

## Variable factories and evaluation

`variable` is a dispatched factory. The supported, useful forms are:

| Form | Meaning |
|---|---|
| `variable("x")` | Input variable. Its `key` is `"x"`; a forward call reads `data["x"]`. |
| `variable()` | Trainable random tensor parameter of shape `(1,)`. |
| `variable(3, 2, display_name="w")` | Trainable random parameter of shape `(3, 2)`. |
| `variable((3, 2), display_name="w")` | Same shape-based trainable parameter form. |
| `variable(tensor, display_name="c")` | Constant/value-backed variable; a tensor with `requires_grad=True` is wrapped as a trainable parameter. |
| `variable([inputs...], callable, display_name="expr")` | Custom symbolic node. Inputs may be Variables, tensors, numbers, or other supported values. |

`display_name` is for representation/plots; `key` is the dictionary identity.
Input variables have `_is_input=True` and appear in `expr.keys`. Value-backed
variables need no input dictionary. A composite expression preserves the keys
of its input variables and evaluates them in topological order:

```python
x, p = variable("x"), variable("p")
residual = x**2 + 0.5 * p - 1
batch = {"x": torch.tensor([[1.0], [2.0]]),
         "p": torch.tensor([[0.2], [0.4]])}
value = residual(batch)
```

Use tensors at the data boundary when gradients or batching matter. Python
numbers are convenient constants and are wrapped when a `Constraint` evaluates,
but a Python/numpy value supplied as a supposed differentiable input is not a
replacement for a `torch.Tensor` with the intended dtype, device, and
`requires_grad` state.

### Operators

Variables overload the arithmetic and indexing needed for expressions:
`+`, `-`, unary `-`, `*`, `@`, `**`, `/`, `//`, `%`, `abs`, indexing/slicing,
`.T`, and `.mT`. PyTorch functions can be applied directly because Variable
implements PyTorch dispatch, for example `torch.sin(x)` or
`torch.linalg.norm(x - y)`. A multi-output expression can be unpacked with
`expr.unpack(nret)` or `expr.unpack(["u", "s", "v"])`.

Custom callables should consume tensors and return tensors. For a module:

```python
net_expr = variable([x], torch.nn.Linear(1, 1), display_name="linear")
```

The module is registered below the Variable and its parameters are visible in
`net_expr.parameters()`.

## Objectives and constraints

### Objectives

`expr.minimize(metric=torch.mean, weight=1.0, name=None)` returns an
`Objective`. The equivalent explicit form is
`Objective(expr, metric=torch.mean, weight=1.0, name=None)`.

- `metric` must produce a differentiable scalar for a normal aggregate loss.
- `weight` scales the metric and may be a Python scalar or scalar tensor.
- `name` is the human-readable term/graph name; it is not necessarily the key
  used by `Objective.forward`.
- The generated `Objective.output_keys[0]` is
  `f"{expr.key}_{metric}"`; inspect `output_keys` rather than guessing it.
- `Objective.forward(input_dict)` returns `{objective.output_keys[0]: weighted_metric}`.

`Objective` also supports scalar multiplication (`2.0 * obj` or `obj * 2.0`).
For the usual training result, consume the aggregate `objective_loss` or
`loss`, not a guessed objective name.

### Comparators

Comparison operators return a `Constraint`; use parentheses around a comparison
before applying the norm or weight:

```python
upper = (x <= 1.0)
lower = (x >= -1.0)
equality = (x == target)
quadratic_upper = (x <= 1.0) ^ 2
weighted = 100.0 * ((x - y) <= p)
```

`<` and `<=` both instantiate `LT`; `>` and `>=` both instantiate `GT`.
`==` instantiates `Eq`. The comparator residuals are deliberately oriented for
violation measurement:

| Syntax | `value` returned by the comparator | violation/penalty |
|---|---|---|
| `left <= right` | `left - right` | `relu(left - right)` |
| `left >= right` | `right - left` | `relu(right - left)` |
| `left == right` | `left - right` | absolute or squared residual |

The `Constraint` forward result has three keys in order:
`[key, f"{key}_value", f"{key}_violation"]`. The first is the weighted scalar
loss; `value` and `violation` retain the element/batch shape. For `LT`/`GT`,
`^1` (the default) computes `mean(relu(value))`; `^2` squares the ReLU before
taking the mean. For `Eq`, `^1` uses L1 loss/absolute residual and `^2` uses
MSE/squared residual. The source comparator classes only define the meaningful
`1` and `2` branches; do not use other norms.

`Constraint` supports multiplication for weights and `^norm` for selecting the
comparator norm. `constraint.update_name("stable_name")` updates the display
name, key, and all three output keys. Merely assigning `constraint.name =
"stable_name"` changes the graph/display name but leaves output keys derived
from the original expression. This distinction matters when reading a
`Problem` result.

### Variable gradients

`neuromancer.gradients.gradient(y, x, grad_outputs=None, create_graph=True)`
computes `dy/dx` with PyTorch autograd. `jacobian(y, x)` is also available.
`expr.grad(other)` constructs a symbolic gradient Variable. `Constraint.grad`
and the loss classes expose convenience methods, but the aggregate loss output
is the most reliable object to differentiate in an integrated Problem.

## Node dictionaries

`Node(callable, input_keys, output_keys, name=None)` wraps a callable whose
arguments and results are tensors. Variable objects are accepted in key lists
and are converted to their `.key` strings.

```python
def affine(p, bias):
    return 2.0 * p + bias

node = Node(affine, ["p", "bias"], ["x"], name="solution_map")
node_out = node({"p": torch.ones(4, 1), "bias": torch.zeros(4, 1)})
# node_out == {"x": tensor(...)}
```

A non-tuple result is wrapped as one output. Tuple results are zipped to
`output_keys`; a result/key count mismatch is not rejected by `Node`, so a
missing result key or silently dropped extra result is a wiring error to catch
in a smoke test. Missing input keys raise `KeyError`. Nodes execute in the
order supplied to `Problem` or `System`; the graph display does not reorder
execution.

A module-backed Node registers its module parameters. `node.freeze()` and
`node.unfreeze()` toggle `requires_grad` for those parameters. A plain Python
lambda has no `.parameters()` method and is not suitable for those methods.

## Aggregate losses

All aggregate losses take `objectives` and `constraints` lists. Their common
output names are:

- `objective_loss`: sum of objective term outputs.
- `penalty_loss`: aggregate constraint contribution.
- `loss`: objective plus constraint contribution for `PenaltyLoss`; the total
  result for the selected method.
- With constraints, `C_values`, `C_violations`, and equality/inequality slices:
  `C_eq_values`, `C_ineq_values`, `C_eq_violations`, and
  `C_ineq_violations`.

`PenaltyLoss(objectives, constraints)` evaluates objectives first, merges their
outputs into the dictionary, evaluates constraints, then sets
`loss = objective_loss + penalty_loss`. It is the default for a small CPU
formulation and the easiest method to inspect.

`BarrierLoss(objectives, constraints, barrier="log10", upper_bound=1.,
shift=1., alpha=0.5)` uses a barrier for feasible inequality residuals
(`value < 0`) and a penalty when the residual is nonnegative. Available barrier
names are `log10`, `log`, `inverse`, `softexp`, `softlog`, and `expshift`; a
callable can also be supplied. The implementation documents `softexp` as the
more numerically stable choice, while log/inverse forms need domain care. Check
that the comparator orientation gives the expected negative feasible residual;
barriers are not a substitute for inspecting equality behavior.

`AugmentedLagrangeLoss(objectives, constraints, train_data, inner_loop=10,
 sigma=2., mu_max=1000., mu_init=0.001, eta=1.0)` maintains per-sample
multipliers and penalty weights. The training path expects `epoch` and `index`
entries in the input dictionary and updates the multipliers every
`inner_loop` epochs; evaluation uses the scaled penalty without that update.
Use it only when the training/data loop supplies this metadata and the
multiplier method is intended. Do not use it as the minimal eager smoke.

Aggregate losses can be added only to another instance of the same aggregate
class; the implementation copies terms and suffixes names to avoid collisions.
Scalar multiplication scales all terms.

## Problem contract and output names

The exact core constructor is:

```python
Problem(nodes, loss, grad_inference=False, check_overwrite=False)
```

`nodes` is a list of Node-like `nn.Module` objects; `loss` is an instantiated
aggregate loss. `grad_inference=True` is stored for training/inference wrappers
that need autograd during evaluation; it does not repair a detached graph.
`check_overwrite=True` emits warnings when a node/loss input or output key would
be overwritten; it is diagnostic, not a repair or hard rejection.

On `problem.step(data)`, each node receives the current dictionary, and its
returned dictionary is merged with `{**old, **new}`. Thus a later output with
the same key overwrites the earlier value. `Problem.graph()` calls
`_check_unique_names()` and requires unique names across all nodes, objectives,
and constraints. Use explicit names even when one unnamed node could receive a
generated `node_1` label.

`Problem.forward(data)` requires `data["name"]` and performs:

1. `step(data)`;
2. `loss(output_dict)`;
3. prefix every returned item as `f'{data["name"]}_{key}'`.

For a batch with `{"name": "train"}`, the aggregate loss is therefore
`output["train_loss"]`, with e.g. `train_objective_loss`,
`train_penalty_loss`, and prefixed constraint diagnostic keys. The original
input and node keys are also present with the same prefix if they survive the
loss dictionary. Always inspect `loss.output_keys`, `constraint.output_keys`,
and the actual returned dictionary when choosing metric names.

## Graph inspection and parameter control

- `problem.graph(include_objectives=True)` returns a `pydot.Dot` graph object
  and also records combined `input_keys`/`output_keys` on the Problem.
- `problem.show(figname=None)` renders a temporary/display PNG; with a suffix
  `.svg`, `.png`, or `.jpg` it writes that format. Rendering needs the optional
  Graphviz executable in addition to the Python `pydot` package. Graph object
  construction and forward evaluation do not require opening a plot.
- `problem.freeze()`/`problem.unfreeze()` delegate to each Node; they control
  node callable parameters, not input batch tensors or symbolic constants.
- `Variable.show(figname=None)` draws the NetworkX expression graph and can
  save a figure.

For a DAG, place producer Nodes before consumer Nodes. For a cyclic rollout,
use `System` from the sibling control route; its `Node` dictionary contract is
the same but it expects time-shaped data and runs the ordered nodes per step.
