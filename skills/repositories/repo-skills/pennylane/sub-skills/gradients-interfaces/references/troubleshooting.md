# Gradients and interfaces troubleshooting

## `qp.grad` returns `()` or warns about no trainable parameters

Cause: Autograd did not see trainable inputs.

Fixes:

- Use `qp.numpy.array(value, requires_grad=True)`.
- Or pass `argnums` to `qp.grad`, `qp.jacobian`, or `qp.value_and_grad`.
- Ensure the differentiated function returns a scalar for `grad`; use `jacobian` for vector-valued outputs.

## Framework array mismatch

Symptoms: conversions fail, gradients are `None`, or interface-specific types disappear.

Fixes:

- Set the QNode `interface` explicitly when auto-detection is ambiguous.
- Use arrays/tensors from one framework for trainable parameters.
- Use `qp.math` in helper code that should work with multiple interfaces.
- Avoid raw Python floats for trainable values unless `argnums` is set and the method supports them.

## Non-differentiable measurements

- Raw `sample` and `counts` are not ordinary analytic scalar outputs; do not expect standard gradients.
- Prefer `expval`, `var`, probabilities, or other differentiable measurements for training.
- Finite-shot expectation gradients can be stochastic; use appropriate tolerances.

## Device/diff method incompatibility

- `diff_method="best"` usually picks a compatible method.
- If forcing a method, confirm the device, operations, measurements, and shots support it.
- Parameter-shift needs supported parametrized operations.
- Backprop/adjoint support is device-dependent.
- Device-provided VJP paths require explicit validation.

## Torch issues

- Install Torch separately; it is not part of the base environment here.
- Use `torch.float64` when comparing against PennyLane defaults or when precision warnings occur.
- For `TorchLayer`, verify `weight_shapes` keys exactly match QNode trainable argument names.
- If `backward()` produces no gradient, check that the Torch tensor has `requires_grad=True` and the QNode returns a differentiable scalar or tensor.

## JAX issues

- Install matching `jax` and `jaxlib` versions for the host/backend.
- With `jax.jit`, static and dynamic arguments matter; set QNode `static_argnums` when needed.
- Avoid Python side effects inside captured/JIT-transformed quantum functions.

## TensorFlow issues

- TensorFlow support is documented as no longer maintained in this snapshot. Avoid new TensorFlow workflows unless required for compatibility.
- If maintaining existing TensorFlow code, pin compatible versions and add focused tests; do not generalize success to new workflows.

## qjit/Catalyst issues

- `qp.qjit` is not a base-PennyLane-only guarantee. Confirm Catalyst is installed and compatible.
- Captured control-flow and dynamic-shape workflows can have restrictions not present in ordinary Python QNodes.
- If qjit fails, first reproduce the circuit without qjit, then add compiler support back incrementally.
