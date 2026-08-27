# Operators and transforms troubleshooting

## Template shape errors

- Check the template signature and expected tensor rank.
- `AngleEmbedding(features, wires, rotation="X")` expects one feature per encoded wire unless using a documented shorter pattern.
- `StronglyEntanglingLayers(weights, wires)` typically needs shape `(n_layers, n_wires, 3)`.
- `AmplitudeEmbedding` may need `normalize=True` or `pad_with=...` if features are not already normalized to the required length.

## Wire-order confusion in matrices

- Always pass `wire_order` to `qp.matrix` for multi-wire operators when comparing with external matrices.
- Custom labels and integer labels must be ordered explicitly.
- Tensor products can be semantically right but matrix-ordered wrong for downstream code.

## Decomposition or compile failures

- A `gate_set` may omit gates needed by an operator's decomposition.
- Some custom or plugin operations lack a decomposition.
- `strict=True` makes `qp.decompose` fail instead of leaving unsupported operations; relax only if partial decomposition is acceptable.
- Work wires may be required for advanced decompositions. Use `num_work_wires` or `minimize_work_wires` deliberately.

## Transform returns `(tapes, processing_fn)`

- This is normal for tape-level transforms.
- Wrap the transform as a decorator or apply it to a QNode when user code expects a callable circuit.
- When debugging transform internals, inspect generated tapes and then call the processing function on device results.

## Custom operator validation failures

- Ensure trainable parameters are positional and wires are passed as `wires=...` to `super().__init__`.
- Store non-trainable behavior in `_hyperparameters`.
- Make `compute_decomposition` static and align its signature with parameters, `wires`, and hyperparameters.
- Implement `_unflatten` for constructors whose arguments cannot be reconstructed by the default pytree metadata.
- Use `pennylane.math` for parameter shape/type checks that must work across Autograd, JAX, and Torch.
- Run `assert_valid(op)` before adding broader tests.

## Differentiability surprises

- Operator construction can accept interface tensors, but a circuit gradient also depends on the QNode interface, measurement type, device, and diff method.
- Route gradient-specific failures to the gradients/interfaces sub-skill.
