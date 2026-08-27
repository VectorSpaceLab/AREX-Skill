# ONNX Text Syntax for Function Bodies and Tests

Use this reference when authoring `FunctionBody(R"ONNX(... )ONNX")` blocks, parser-based tests, or compact graph/function fixtures.

## Core conventions

- Keep scalar attributes near the operator call: `Y = Transpose<perm = [2, 0, 1]>(X)`.
- Put subgraph attributes after the input list for readability.
- Function body attributes may reference outer attributes with `@attr_name` when the schema declares that attribute.
- Names inside a function body or subgraph must not collide with declared inputs/outputs or with outer-scope names visible to that subgraph.

## Practical patterns

```text
<ir_version: 8, opset_import: ["" : 14]>
g (float[2, 3] X) => (float[2, 3] Y) {
  Y = Relu(X)
}
```

```text
scan_body (float[1] s, float[1] x) => (float[1] so, float[1] xo) {
  so = Identity(s)
  xo = Identity(x)
}
```

## Gotchas

- ONNX text syntax is not protobuf text format.
- `@attr_name` is only valid inside a function body and only for declared attributes.
- Optional values use empty names or `Optional`/`OptionalGetElement` when the type is dynamic optional.
- Control-flow subgraphs should define their own inputs/outputs explicitly.
- If a test or function body becomes unwieldy, move the explanation into a nearby reference and keep the runtime file compact.
