# Gradients and interfaces workflows

## Autograd / PennyLane NumPy

```python
import pennylane as qp

dev = qp.device("default.qubit", wires=1)

@qp.qnode(dev, interface="autograd")
def circuit(theta):
    qp.RX(theta, 0)
    return qp.expval(qp.Z(0))

theta = qp.numpy.array(0.2, requires_grad=True)
value, grad = qp.value_and_grad(circuit)(theta)
```

Use `requires_grad=True` or `argnums` for scalar Python values.

## JAX workflow

```python
import jax
import jax.numpy as jnp
import pennylane as qp

dev = qp.device("default.qubit", wires=1)

@qp.qnode(dev, interface="jax")
def circuit(theta):
    qp.RX(theta, 0)
    return qp.expval(qp.Z(0))

print(jax.grad(circuit)(jnp.array(0.2)))
```

Only use this after JAX/JAXLIB are installed. If combining with `jit`, verify static arguments and supported operations.

## Torch workflow

```python
import torch
import pennylane as qp

dev = qp.device("default.qubit", wires=1)

@qp.qnode(dev, interface="torch")
def circuit(theta):
    qp.RX(theta, 0)
    return qp.expval(qp.Z(0))

theta = torch.tensor(0.2, dtype=torch.float64, requires_grad=True)
value = circuit(theta)
value.backward()
print(theta.grad)
```

PennyLane QNodes may promote Torch `float32` inputs to `float64`; budget memory accordingly.

## TorchLayer

```python
import torch
import pennylane as qp

dev = qp.device("default.qubit", wires=2)

@qp.qnode(dev, interface="torch")
def qnode(inputs, weights):
    qp.AngleEmbedding(inputs, wires=[0, 1])
    qp.StronglyEntanglingLayers(weights, wires=[0, 1])
    return qp.expval(qp.Z(0))

layer = qp.qnn.TorchLayer(qnode, weight_shapes={"weights": (1, 2, 3)})
print(layer(torch.zeros(2, dtype=torch.float64)))
```

Check that every trainable QNode argument except data inputs has a corresponding `weight_shapes` entry.

## Choose a differentiation method

- Start with `diff_method="best"`.
- Use parameter-shift for analytic gradients of supported parametrized gates and measurements.
- Use finite differences for fallback numerical checks or non-analytic operations.
- Use backprop/adjoint only when the device supports it and the result type is compatible.
- Use SPSA for stochastic/noisy settings where analytic gradients are not viable.

## Gradient validation pattern

Use a known one-qubit circuit to verify signs and trainability:

```python
dev = qp.device("default.qubit", wires=1)
@qp.qnode(dev)
def cos_circuit(x):
    qp.RX(x, 0)
    return qp.expval(qp.Z(0))

x = qp.numpy.array(0.123, requires_grad=True)
assert qp.math.allclose(cos_circuit(x), qp.numpy.cos(x))
assert qp.math.allclose(qp.grad(cos_circuit)(x), -qp.numpy.sin(x))
```

This catches missing trainable flags, wrong interface selection, and measurement incompatibility.
