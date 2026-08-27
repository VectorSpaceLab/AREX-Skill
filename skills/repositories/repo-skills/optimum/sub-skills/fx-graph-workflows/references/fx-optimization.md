# Optimum FX optimization workflows

This reference covers the CPU-compatible part of Optimum's FX graph surface. Facts here were distilled from the package source, user-facing FX docs, installed API inspection, and transformation behavior tests. It is intentionally self-contained; use the bundled smoke script for local verification rather than relying on source-checkout tests.

## API surface to import

```python
from optimum.fx.optimization import (
    Transformation,
    ReversibleTransformation,
    compose,
    MergeLinears,
    FuseBiasInLinear,
    ChangeTrueDivToMulByInverse,
    FuseBatchNorm2dInConv2d,
    FuseBatchNorm1dInLinear,
)
from optimum.fx.utils import are_fx_features_available
```

`are_fx_features_available()` checks the Transformers FX compatibility gate used by Optimum. If it is false, upgrade to a Transformers version that exposes the expected FX tracing utilities before attempting Transformers-model tracing. Plain `torch.fx.symbolic_trace` on a local PyTorch module can still be useful for small smoke checks when the Optimum optimization package imports successfully.

## GraphModule contract

Optimum FX transformations operate on `torch.fx.GraphModule`, not on an untraced `torch.nn.Module`.

Expected pattern:

1. Put the model in the right mode before tracing. For computation-preserving inference rewrites, use `model.eval()`; this matters for BatchNorm fusion.
2. Trace into a `GraphModule`:
   - Small local modules: `torch.fx.symbolic_trace(model)`.
   - Transformers modules: use the Transformers FX tracer with explicit `input_names` when needed.
3. Pass the traced module to a transformation object as a callable.
4. Keep the same input signature when comparing original and transformed outputs.
5. After graph edits, the graph must lint and the module must recompile. Optimum transformation calls do this by default.

`Transformation.__call__(graph_module, lint_and_recompile=True)` runs `transform(...)`, then `graph_module.graph.lint()` and `graph_module.recompile()` unless the flag is disabled. Disable lint/recompile only when composing several transformations and doing one final lint/recompile at the end.

`ReversibleTransformation.__call__(graph_module, lint_and_recompile=True, reverse=False)` uses `transform(...)` by default and `reverse(...)` when `reverse=True`. Reverse is only safe on a graph that still carries the transformation's node markers and graph/module structure.

Most built-ins mutate the input `GraphModule` in place. Use `compose(..., inplace=False)` when you need a transformed copy.

## Base transformation classes

### `Transformation`

Subclass this for one-way graph changes.

Required method:

```python
def transform(self, graph_module: torch.fx.GraphModule) -> torch.fx.GraphModule:
    ...
```

Useful attributes and helpers:

- `preserves_computation`: `False` by default. Set to `True` only when transformed outputs should match original outputs.
- `signature`: hash derived from the transformation class and instance attributes.
- `mark_as_transformed(node)`: attach this transformation's signature to a node.
- `transformed(node)`: test whether a node was marked by this transformation instance/signature.
- `get_transformed_nodes(graph_module)`: return marked nodes in the graph.

### `ReversibleTransformation`

Subclass this when a graph can be restored.

Required methods:

```python
def transform(self, graph_module): ...
def reverse(self, graph_module): ...
```

Use the same transformation instance, or the same composed transformation object, for forward and reverse calls whenever possible. Reverse implementations depend on marker metadata and sometimes additional attributes stored on transformed nodes.

## `compose(...)`

`compose(*transformations, inplace=True)` creates one transformation that applies the supplied transformations in the order written:

```python
chain = compose(ChangeTrueDivToMulByInverse(), MergeLinears())
transformed = chain(traced)
```

Key behavior:

- If every element is a `ReversibleTransformation`, the composed object is reversible and `chain(transformed, reverse=True)` runs reverse transformations in the correct opposite order.
- If any element is one-way, the composed object is one-way.
- `chain.preserves_computation` is true only when all members declare `preserves_computation=True`.
- `inplace=True` mutates the input graph module.
- `inplace=False` deep-copies the graph module before applying the chain. This is the safest option when the caller needs to keep the original traced graph intact.

## Built-in transformations

### `MergeLinears`

- Type: reversible.
- `preserves_computation=True`.
- Merges multiple `torch.nn.Linear` call-module nodes that consume the same input node into one larger `Linear` module.
- Rewrites the original linear call nodes into `operator.getitem` slices of the merged output.
- Stores original target names on the merged node so `reverse=True` can recreate the original linears and delete the merged module.
- If some merged linears have bias and others do not, the transform warns because missing biases are effectively treated as zeros.

Use when a graph has parallel linear projections from the same tensor, such as query/key/value style projections. Verify that output values and restored parameters match.

### `FuseBiasInLinear`

- Type: reversible.
- `preserves_computation=True`.
- For each `torch.nn.Linear` with a bias, appends a constant-one feature to the linear input and concatenates the bias as an extra column in the weight.
- Sets the module bias to `None` after fusion.
- Stores the inserted-node range and original input node so `reverse=True` can erase inserted helper nodes and restore the weight/bias split.

Use when a backend wants bias folded into weight. Verify outputs before and after fusion and after restoration.

### `ChangeTrueDivToMulByInverse`

- Type: reversible.
- `preserves_computation=True`.
- Changes `operator.truediv` nodes to `operator.mul` only when the denominator is static, not another FX node.
- Forward rewrite: `x / y` becomes `x * (1 / y)`.
- Reverse rewrite: `x * inv_y` becomes `x / (1 / inv_y)` for nodes marked by this transformation.

This is the safest transformation to use for local CPU smoke checks because it needs no model downloads or special submodules.

### `FuseBatchNorm2dInConv2d`

- Type: one-way `Transformation`.
- `preserves_computation=True` for evaluation-mode inference graphs.
- Fuses a `torch.nn.BatchNorm2d` immediately following a `torch.nn.Conv2d` into the convolution weights and bias.
- Only fuses when the convolution output is used solely by the BatchNorm node. If the conv output fans out to another user, fusion is skipped.
- Deletes the BatchNorm module and erases its graph node.

Use only with `model.eval()` and stable BatchNorm running statistics.

### `FuseBatchNorm1dInLinear`

- Type: one-way `Transformation`.
- `preserves_computation=True` for evaluation-mode inference graphs.
- Handles both `Linear -> BatchNorm1d` and `BatchNorm1d -> Linear` when there is no unsafe fanout and the relevant feature dimensions align.
- Deletes the fused BatchNorm module and rewires graph uses.
- Does not handle every possible 3D tensor layout; if dimensions do not match the expected feature axis, fusion is skipped.

Use only with `model.eval()` and explicit output comparisons.

## Computation-preserving checks

For transformations with `preserves_computation=True`, verify behavior with the exact inputs the transformed graph will receive:

```python
model.eval()
traced = torch.fx.symbolic_trace(model)
with torch.no_grad():
    expected = model(*args, **kwargs)
    transformed = transformation(traced)
    actual = transformed(*args, **kwargs)
torch.testing.assert_close(actual, expected, rtol=1e-4, atol=1e-5)
```

For nested outputs, flatten tensors before comparing. Ignore non-tensor metadata unless it is part of the user's correctness requirement.

Also check the graph/module structure that the transform promises to change:

- `ChangeTrueDivToMulByInverse`: fewer `operator.truediv` nodes and more `operator.mul` nodes.
- `MergeLinears`: fewer individual `Linear` modules in the targeted block, then restored count after `reverse=True`.
- `FuseBiasInLinear`: linear modules have no bias after transform, then original bias is restored after `reverse=True`.
- BatchNorm fusions: BatchNorm modules are removed only for eligible adjacent, sole-use patterns.

## Reversible chain pattern

Use a single composed object and keep original test inputs:

```python
chain = compose(ChangeTrueDivToMulByInverse(), FuseBiasInLinear(), inplace=False)
transformed = chain(traced)
# compare transformed output to baseline
restored = chain(transformed, reverse=True)
# compare restored output and restored parameter names/values to baseline
```

When validating restoration, compare:

- Output tensors on representative inputs.
- `transformed.code` and `restored.code` when graph text stability matters.
- Named parameter key sets and tensor values when transformations altered modules.

## Native tests and downloads

Source transformation tests include useful behavior checks but some cases instantiate tiny Transformers models from model identifiers. Those can require network access or a pre-populated model cache. Prefer the bundled `scripts/fx_transform_smoke.py` for required local validation. Run native model tests only when model downloads/cache use is explicitly allowed by the task and environment.
