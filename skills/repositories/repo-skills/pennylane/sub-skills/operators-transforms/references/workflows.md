# Operators and transforms workflows

## Compose observables

```python
import pennylane as qp

hamiltonian = 0.5 * qp.PauliZ(0) + 0.25 * (qp.PauliX(0) @ qp.PauliX(1))
print(qp.simplify(hamiltonian))
print(qp.matrix(hamiltonian, wire_order=[0, 1]))
```

Use `@`/`qp.prod` for tensor products and `+`/`qp.sum` for sums. For exact coefficient/operator lists, `qp.dot(coeffs, ops)` is often clearer.

## Choose a template and validate shapes

```python
n_wires = 3
n_layers = 2
weights = qp.numpy.zeros((n_layers, n_wires, 3))

@qp.qnode(qp.device("default.qubit", wires=n_wires))
def ansatz(features, weights):
    qp.AngleEmbedding(features, wires=range(n_wires), rotation="Y")
    qp.StronglyEntanglingLayers(weights, wires=range(n_wires))
    return qp.probs(wires=range(n_wires))
```

When a template raises a shape error, inspect the template signature and documented shape helper before changing code. Do not flatten arrays blindly.

## Decompose to a gate set

```python
@qp.qnode(qp.device("default.qubit", wires=2))
def circuit(x):
    qp.Rot(x, x / 2, -x, wires=0)
    qp.CNOT([0, 1])
    return qp.expval(qp.Z(1))

decomposed = qp.transforms.decompose(circuit, gate_set={"RX", "RY", "RZ", "CNOT"})
print(qp.draw(decomposed)(0.2))
```

If strict decomposition fails, the target gate set may be incomplete or a template/operator may not define the required decomposition.

## Compile a circuit

```python
compiled = qp.compile(circuit, basis_set={"RX", "RY", "RZ", "CNOT"}, num_passes=2)
print(qp.draw(compiled)(0.2))
```

Compilation may commute controls, cancel inverses, merge rotations, and remove barriers by default. Explain which level of the circuit the user is viewing.

## Create a custom operator

```python
class FlipAndRotate(qp.operation.Operation):
    # Set to "A" only when the operator also defines a generator,
    # parameter_frequencies, or grad_recipe compatible with parameter-shift.
    grad_method = None

    def __init__(self, angle, wire_rot, wire_flip=None, do_flip=False):
        if do_flip and wire_flip is None:
            raise ValueError("Expected a wire to flip; got None.")
        self._hyperparameters = {"do_flip": do_flip}
        wires = qp.wires.Wires(wire_rot) + qp.wires.Wires(wire_flip)
        super().__init__(angle, wires=wires)

    @property
    def num_params(self):
        return 1

    @staticmethod
    def compute_decomposition(angle, wires, do_flip):
        ops = []
        if do_flip:
            ops.append(qp.PauliX(wires=wires[1]))
        ops.append(qp.RX(angle, wires=wires[0]))
        return ops

    @classmethod
    def _unflatten(cls, data, metadata):
        wires = metadata[0]
        hyperparameters = dict(metadata[1])
        wire_flip = wires[1] if len(wires) > 1 else None
        return cls(data[0], wire_rot=wires[0], wire_flip=wire_flip, **hyperparameters)
```

Then validate:

```python
from pennylane.ops.functions import assert_valid
assert_valid(FlipAndRotate(0.1, wire_rot=0, wire_flip=1, do_flip=True), skip_capture=True)
```

Use plain `assert_valid(op)` or a JAX-marked test when validating program capture as part of source changes. For repo changes, add tests under the matching `tests/ops/` or `tests/templates/` subdirectory and follow the development sub-skill.
