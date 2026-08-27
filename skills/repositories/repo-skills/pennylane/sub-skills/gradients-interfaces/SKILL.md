---
name: gradients-interfaces
description: "Configure PennyLane gradients, differentiable interfaces,
  optimizers, TorchLayer, and optional compiler/qjit workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Gradients and interfaces

Use this sub-skill when a task involves differentiating QNodes, choosing `diff_method`, using Autograd/JAX/Torch/TensorFlow arrays, training hybrid models, converting QNodes to `TorchLayer`, or troubleshooting gradient/interface behavior.

## Read first

- [`references/api-reference.md`](references/api-reference.md): gradient, interface, optimizer, math, QNN, and qjit API facts.
- [`references/workflows.md`](references/workflows.md): Autograd, JAX, Torch, TorchLayer, and finite-difference/parameter-shift patterns.
- [`references/troubleshooting.md`](references/troubleshooting.md): trainability warnings, interface mismatch, non-differentiable measurements, optional framework failures, and Catalyst caveats.
- [`scripts/interface_gradient_smoke.py`](scripts/interface_gradient_smoke.py): base Autograd gradient smoke that does not require optional ML frameworks.
- [`scripts/torchlayer_probe.py`](scripts/torchlayer_probe.py): optional TorchLayer probe; it exits clearly if Torch is not installed.

## Route within this sub-skill

- **Base gradients:** use `qp.grad`, `qp.jacobian`, `qp.value_and_grad`, `qp.vjp`, `qp.jvp`, and gradient transforms under `qp.gradients`.
- **Interface selection:** set `interface="auto"`, `"autograd"`, `"jax"`, `"torch"`, or legacy `"tf"` deliberately when auto-detection is ambiguous.
- **Differentiation method:** start with `diff_method="best"`; choose parameter-shift, finite-diff, backprop, adjoint, SPSA, or device-specific methods only when the device/measurement/workflow requires it.
- **Training loops:** use PennyLane optimizers for Autograd/NumPy workflows; use native JAX/Torch optimizers for those frameworks.
- **QNN:** use `qp.qnn.TorchLayer(qnode, weight_shapes, init_method=None)` when integrating a QNode into `torch.nn`.
- **Compilation:** `qp.qjit` routes to Catalyst-backed workflows; do not claim qjit availability until Catalyst runtime is installed and checked.

## Boundaries

- Circuit/device construction belongs to [`../circuits-devices/SKILL.md`](../circuits-devices/SKILL.md).
- Operator/template shape and custom-operator details belong to [`../operators-transforms/SKILL.md`](../operators-transforms/SKILL.md), but gradient method compatibility may be handled here.
- Resource estimation and qchem/domain algorithms belong to [`../applications-qchem-resource/SKILL.md`](../applications-qchem-resource/SKILL.md).
- Source test markers and lint rules belong to [`../repo-development/SKILL.md`](../repo-development/SKILL.md).

## Minimal Autograd pattern

```python
import pennylane as qp

dev = qp.device("default.qubit", wires=1)

@qp.qnode(dev)
def circuit(theta):
    qp.RX(theta, wires=0)
    return qp.expval(qp.Z(0))

theta = qp.numpy.array(0.2, requires_grad=True)
print(circuit(theta))
print(qp.grad(circuit)(theta))
```

If `qp.grad` returns `()` or warns about no trainable parameters, use a trainable PennyLane NumPy tensor or pass `argnums` explicitly.

## Verification cues

State the array framework, QNode `interface`, `diff_method`, measurement type, shot setting, optional dependency status, and a numeric gradient check. For source changes, choose focused tests under `tests/gradients/`, `tests/test_grad.py`, interface-marked tests, or `tests/qnn/` depending on the changed surface.
