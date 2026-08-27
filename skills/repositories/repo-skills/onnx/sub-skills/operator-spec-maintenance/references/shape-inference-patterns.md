# ONNX Shape Inference Patterns

## Named helper pattern

Prefer a named helper in the schema file over an inline lambda so breakpoints and review are easier.

```cpp
static void InferShapeForMyOp(InferenceContext& ctx) {
    propagateElemTypeFromInputToOutput(ctx, 0, 0);
    if (!hasNInputShapes(ctx, 1)) {
        return;
    }
    // inspect dimensions safely here
}
```

## Safe dimension handling

- Check `hasNInputShapes(ctx, n)` or `hasInputShape(ctx, i)` before touching shapes.
- Check `has_dim_value()` before reading a dimension value.
- Leave unknown dimensions unset instead of inventing values.
- Preserve symbolic dimensions when possible.
- Use `checkInputRank`, `unifyInputDim`, `unifyInputShape`, `unifyInputShapePrefix`, and `updateOutputShape` for common cases.

## Common workflow patterns

- Unary elementwise ops can often use `propagateShapeAndTypeFromFirstInput`.
- Binary broadcasting ops often need a broadcast helper and an output-shape update.
- Shape-changing ops should check rank, read attributes, and build the output shape explicitly.
- Heterogeneous variadic ops require explicit type propagation for each input/output.

## Testing guidance

- Add focused Python shape-inference tests for known shapes, partial shapes, rank inference, and error cases.
- For tricky free-dimension assertions in C++ tests, remember that unset dims may materialize as `unk__*` placeholders after inference.
- For parser-based function-body tests, use compact ONNX text fixtures instead of verbose Python graph construction when the syntax is the real behavior under test.
