# Symbolic-problem troubleshooting

## Import and API lookup

**Symptom:** `neuromancer.Variable` or another class is unavailable from a
short top-level import.

**Recovery:** check the installed distribution version, then use the module
paths `neuromancer.constraint.variable`, `neuromancer.loss.PenaltyLoss`,
`neuromancer.system.Node`, and `neuromancer.problem.Problem`. The package
exposes these modules; direct star exports are not a safe portability
assumption.

## Duplicate keys and names

**Symptom:** an assertion says a Variable key repeats, a Problem graph says
nodes/objectives/constraints do not have unique names, or a later node appears
to receive the wrong tensor.

**Recovery:**

- Give each input Variable a unique key. A composite expression may reuse an
  input key intentionally, but do not create a second input Variable with the
  same key in one expression graph.
- Give every Node, Objective, and Constraint a unique explicit `name`.
- Keep producer output keys distinct from batch keys unless the overwrite is a
  deliberate recurrent update. `Problem` merges dictionaries with later
  values winning.
- Construct with `check_overwrite=True`; it emits a warning, but it does not
  prevent the overwrite. Rename the producer or consumer and re-run the graph.
- If a constraint's generated output key is colliding, call
  `constraint.update_name("unique_constraint")`. Assigning only
  `constraint.name` changes its label, not its key/output keys.

## Missing dictionary keys and ordering

**Symptom:** `KeyError` during a Variable, Node, or Problem forward pass.

**Recovery:** print/check `expr.keys`, `node.input_keys`, and each loss term's
`input_keys`. Supply every input key as a tensor in the merged batch. For a
Problem, also supply a string `data["name"]`. Put producer Nodes before
consumers; `Problem` and `System` execute list order and do not topologically
sort the call sequence. A Node that declares an input key it does not use
still attempts to read that key.

A Node only returns the keys paired by `zip(output_keys, callable_result)`.
Make a callable return one tensor for one output key or a tuple with exactly the
number of declared outputs. Extra tuple elements are dropped and missing
ones do not produce a key.

## Non-tensor values, dtype, and shape

**Symptom:** an arithmetic operation, comparator, or module fails with a type,
device, broadcasting, or matrix-shape error; the result does not require grad.

**Recovery:** convert external values at the batch boundary with
`torch.as_tensor`/`torch.tensor`, use a consistent floating dtype and device,
and make differentiable inputs `requires_grad=True` where the task needs input
gradients. Keep ordinary Node tensors `(batch, features)` for this route and
check slices such as `x[:, [0]]` preserve the feature dimension. Python scalars
are appropriate constants, not substitutes for a trainable/input tensor.

Do not call `.numpy()`, `.item()`, or `.detach()` on a value before a symbolic
objective/constraint or autograd residual that must backpropagate. If a module
expects a particular feature width, check the Node input tensor against it.

## Comparator orientation and norm

**Symptom:** a supposedly feasible inequality has a positive residual or a
constraint penalizes the wrong side.

**Recovery:** rewrite the expression in mathematical form and inspect the
returned `<constraint-key>_value`:

- `left <= right` is feasible when `left - right <= 0`.
- `left >= right` is feasible when `right - left <= 0`.
- equality has residual `left - right`; it is feasible at zero.

Use `^1` for mean ReLU/absolute behavior and `^2` for squared violations.
Parenthesize the comparator before `^2`, for example `(x <= b) ^ 2`.
`<`/`>` and `<=`/`>=` share the same implementation; this is a penalty
calculation, not a strict-feasibility solver.

## Loss output naming and missing metrics

**Symptom:** `output["train_obj"]` or `output["train_my_constraint"]` is
missing even though the term has that `.name`.

**Recovery:** inspect `obj.output_keys` and `constraint.output_keys`. Objective
term keys are generated from the expression key and metric; Constraint keys are
generated from its operands/comparator unless `update_name()` was used. The
aggregate names are stable: `objective_loss`, `penalty_loss`, `loss`, plus
constraint matrices/diagnostics when constraints exist. `Problem.forward`
prefixes all of them with the batch name, so use `output["train_loss"]` for a
batch named `train`.

If `_check_keys` reports an output/input collision inside an aggregate loss,
rename the expression/constraint or use `update_name` before constructing the
loss. Avoid relying on `Objective.grad` with an ad-hoc name; differentiate the
actual aggregate output or inspect the generated objective key first.

## Barrier and augmented-Lagrange failures

**Symptom:** `BarrierLoss` produces NaN/Inf or a seemingly feasible point gets a
barrier penalty.

**Recovery:** verify the inequality residual sign first. The implementation
uses a barrier for `value < 0` and a penalty for `value >= 0`; log/inverse forms
are domain-sensitive. Try the documented `softexp` option, keep values finite,
and avoid using a barrier as a repair for an equality or reversed comparator.

**Symptom:** `AugmentedLagrangeLoss` fails looking up `epoch` or `index`, or its
sample buffers have the wrong length.

**Recovery:** pass the required training DataLoader as `train_data`, ensure its
dataset length matches the intended sample indexing, and provide `epoch` and
`index` in training batches. Use evaluation mode or `PenaltyLoss` for a tiny
forward check; multiplier updates are intentionally stateful and occur every
`inner_loop` epochs.

## Graph rendering and optional Graphviz

**Symptom:** `problem.graph()` works but `problem.show()` cannot render a PNG,
SVG, or JPG.

**Recovery:** distinguish graph construction from rendering. Keep using the
returned `pydot.Dot` for structural validation. Install/configure the optional
Graphviz executable only when visual output is required, and write to a
writable location. `Variable.show()` uses NetworkX/matplotlib and is likewise
optional for headless CPU checks. Do not make plotting a prerequisite for a
forward pass.

## Detached gradients and frozen modules

**Symptom:** aggregate `loss` is a tensor but `requires_grad=False`,
`backward()` fails, or Node parameters have no gradients.

**Recovery:**

1. Check `output["<batch-name>_loss"].requires_grad` before backward.
2. Ensure tensors passed into the Node and Variables are connected to the
   module/parameter you intend to optimize.
3. Remove premature `.detach()`, `.item()`, NumPy conversion, or a
   `torch.no_grad()` context from the path.
4. Call `problem.unfreeze()` after intentionally freezing module-backed Nodes.
5. Use `grad_inference=True` only when a wrapper needs gradients during
   evaluation; it cannot reconnect a graph that was detached.
6. Remember that a plain lambda Node has no registered parameters. Use a
   `torch.nn.Module` callable if parameter gradients are expected.

For PDE/ODE residuals involving coordinate derivatives, route to the sibling
[`../../dynamics-modeling/SKILL.md`](../../dynamics-modeling/SKILL.md), where
`requires_grad` and higher-order derivative details are owned.

## Out-of-scope routing

If the failure is in normalization, sequence length, split/collation, or
Trainer/Lightning hooks, route to
[`../../data-training/SKILL.md`](../../data-training/SKILL.md). If it is in
rollout time axes, PSL signals, or preview feedback, route to
[`../../control-simulation/SKILL.md`](../../control-simulation/SKILL.md). If it
is a structured-map dimension or native accelerator extension issue, route to
[`../../structured-operators/SKILL.md`](../../structured-operators/SKILL.md).
