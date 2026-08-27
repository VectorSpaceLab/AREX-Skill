# Gradients and interfaces API reference

## Gradient helpers

Verified signatures:

```python
qp.grad(func, argnums=None, h=None, method=None)
qp.jacobian(func, argnums=None, method=None, h=None)
qp.value_and_grad(func, argnums=0, method=None, h=None)
qp.metric_tensor(tape, argnum=None, approx=None, allow_nonunitary=True,
                 aux_wire=None, device_wires=None)
```

Other exposed helpers include `qp.vjp` and `qp.jvp`. The `pennylane.gradients` module includes parameter-shift, finite difference, SPSA, hadamard gradients, metric tensor, VJP/JVP transforms, and Hessian-related transforms.

## QNode differentiation knobs

`QNode` and `qnode` support:

- `interface="auto"` by default.
- `diff_method="best"` by default.
- `grad_on_execution="best"`.
- `max_diff=1` for derivative order.
- `device_vjp=False` and `gradient_kwargs=None` for advanced paths.
- `static_argnums=()` for arguments that should be static in capture/JAX-style workflows.

Choose these based on the device, measurement, and framework rather than setting everything manually.

## Interfaces

Documented interface families in this snapshot:

- NumPy/Autograd: built-in base path with `qp.numpy` tensors and PennyLane optimizers.
- JAX: native JAX arrays and transformations when JAX is installed.
- Torch: `torch.Tensor` and native Torch optimizers when Torch is installed.
- TensorFlow: documented as no longer maintained as of PennyLane v0.44; maintain existing code carefully and prefer JAX/Torch for new workflows.

Use `qp.math` for interface-agnostic math in PennyLane-facing code. Avoid raw NumPy in source code that may receive trainable JAX/Torch/Autograd objects.

## Optimizers

PennyLane exposes built-in optimizers for NumPy/Autograd-style workflows, including gradient descent, Adam, momentum, RMSProp, natural-gradient, Rotosolve/Rotoselect, SPSA, shot-adaptive, and QNSPSA families.

For JAX or Torch training, use native framework optimizers unless a PennyLane-specific optimizer explicitly supports the chosen interface.

## TorchLayer

Verified signature:

```python
qp.qnn.TorchLayer(qnode, weight_shapes, init_method=None)
```

Requirements:

- Torch must be installed.
- The QNode must accept data inputs and named trainable weight arguments that match `weight_shapes`.
- QNode return shapes must be compatible with `torch.nn` module output expectations.

## qjit/Catalyst

`qp.qjit` is imported from `pennylane.compiler`. It is a facade for compiler-backed workflows. Treat it as optional unless Catalyst and its dependencies are installed and checked. Do not use `qjit` as a generic speed fix for ordinary Python QNodes without validating compatibility.

## Program capture and control flow

`pennylane.capture`, `pennylane.control_flow.for_loop`, and `while_loop` support advanced program capture and dynamic/captured workflows. These are often JAX-adjacent and should be tested with the exact framework/runtime selected by the user.
