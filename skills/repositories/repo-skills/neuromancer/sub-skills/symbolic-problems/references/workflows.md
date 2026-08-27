# Symbolic formulation workflows

## 1. Build a constrained parametric solution map

Use this sequence for L2O-style parametric programming. It keeps parameters in
the batch and lets a trainable Node produce the decision variables.

1. **Name the interface.** Choose batch keys such as `p`, `a`, or `p1`, and a
   single Node output such as `x`. Decide the batch shape, normally
   `(batch, features)`.
2. **Wrap the map.** Construct a PyTorch callable (a linear layer is enough for
   a smoke) and wrap it as `Node(map_module, ["p"], ["x"], name="map")`.
   Multi-input maps list all keys and the callable argument order must match.
3. **Slice decisions symbolically.**
   ```python
   xvec = variable("x")
   x1, x2 = xvec[:, [0]], xvec[:, [1]]
   p = variable("p")
   a = variable("a")
   ```
4. **Write the objective.** For example, the parametric Rosenbrock form from
   the public formulation is
   ```python
   f = (1 - x1)**2 + a * (x2 - x1**2)**2
   obj = f.minimize(metric=torch.mean, weight=1.0, name="objective")
   ```
5. **Write constraints in residual orientation.** For
   `g(x) <= b`, write `g(x) <= b`; for `g(x) >= b`, write `g(x) >= b`.
   Example annulus and ordering constraints:
   ```python
   c_order = (x1 >= x2)
   c_inner = ((p / 2)**2 <= x1**2 + x2**2)
   c_outer = (x1**2 + x2**2 <= p**2)
   ```
   Add weights with `100.0 * c` and choose a norm with `(c)^2` when desired.
6. **Select and instantiate one aggregate loss.** Start with
   `PenaltyLoss([obj], [c_order, c_inner, c_outer])`. Give terms unique names;
   use `update_name` if a constraint's output keys must be stable.
7. **Construct the Problem and validate once.**
   ```python
   problem = Problem([map_node], loss, check_overwrite=True)
   problem.graph()  # structural check; plotting is optional
   ```
8. **Evaluate a named batch.**
   ```python
   batch = {"p": torch.rand(8, 1), "a": torch.rand(8, 1), "name": "train"}
   output = problem(batch)
   total = output["train_loss"]
   assert total.ndim == 0 and total.requires_grad
   ```
   Backpropagate only after checking `requires_grad` and the expected finite
   values. A trainer may use `train_loss`, `dev_loss`, etc. according to its
   data wrapper, but the core `Problem` prefix is the batch `name`.

This is formulation only: sampling/splitting/data loaders belong to
[`../../data-training/SKILL.md`](../../data-training/SKILL.md), while neural
ODEs or rollout models belong to
[`../../dynamics-modeling/SKILL.md`](../../dynamics-modeling/SKILL.md) and
[`../../control-simulation/SKILL.md`](../../control-simulation/SKILL.md).

## 2. Tiny CPU graph validation

Before a long optimization run, use a deterministic batch and check:

- every Node input key is present;
- every Node output count matches its declared output keys;
- producer Nodes precede consumer Nodes;
- all Node/objective/constraint names are unique;
- all symbolic expression keys are present in the merged dictionary;
- `problem.graph()` succeeds even if Graphviz rendering is unavailable;
- the result contains `<batch-name>_loss`, and it is a scalar with a gradient;
- one backward pass creates gradients on a module-backed Node parameter;
- constraint diagnostics have expected signs and shapes.

The bundled `scripts/core_smoke.py --run` performs a MLP-free version of these
checks without a dataloader, download, optimizer loop, or generated files.

## 3. Loss-method selection

| Need | Use | Validation to perform |
|---|---|---|
| Simple weighted objectives and violations; eager CPU check | `PenaltyLoss` | Verify objective/penalty signs and `loss == objective_loss + penalty_loss`. |
| Interior inequality treatment with a barrier | `BarrierLoss` | Confirm feasible inequality `value` is negative; select a stable barrier and watch finite values near the boundary. |
| Multiplier updates over a training data loader | `AugmentedLagrangeLoss` | Supply `train_data`, and verify `epoch`, `index`, sample count, and constraint dimensions before entering training mode. |

Do not swap methods merely to hide an incorrectly oriented comparator. A
constraint's residual is the first debugging signal.

## 4. Graph and parameter lifecycle

1. Build the graph with explicit names.
2. Call `problem.graph()` and inspect the returned `pydot.Dot`; this is safer
   than immediately calling `show()`.
3. Call `problem.show("problem.svg")` only when a Graphviz renderer and a
   writable output location are available.
4. Use `problem.freeze()` for module-backed Nodes when optimizing only another
   part of a larger graph, then `unfreeze()` before joint training. Do not call
   these methods on lambda-backed Nodes.
5. If the graph is a time rollout or contains feedback keys, hand it to the
   `System`/control route rather than trying to make `Problem` execute a cycle.

## 5. Synthetic difficult case: collision then repair

A useful usability check beyond the basic tests is a two-input map with a
collision and a missing key:

1. Create `Node(lambda p: p, ["p"], ["p"], name="map")` and construct a
   constraint whose symbolic output is also named `p`. Instantiate
   `Problem(..., check_overwrite=True)` and confirm the warning/overwriting
   risk is visible.
2. Deliberately call the Node with a batch missing `p` and confirm `KeyError`.
3. Repair the map output to `x`, give the constraint a unique name/output via
   `update_name("bound")`, provide `p` as a tensor, and evaluate a tiny
   `PenaltyLoss` Problem.
4. Assert that `<name>_loss`, objective/constraint diagnostics, and a
   differentiable scalar are present.

This case tests key ownership, naming, and recovery rather than only a happy
path. Materialize it under the verification artifact area, not in this
runtime tree.
