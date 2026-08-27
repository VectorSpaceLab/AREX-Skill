# Circuits and devices workflows

## Create a basic QNode

```python
import pennylane as qp

params = qp.numpy.array([0.2, -0.1], requires_grad=True)
dev = qp.device("default.qubit", wires=["control", "target"])

@qp.qnode(dev)
def circuit(x):
    qp.RX(x[0], wires="control")
    qp.CNOT(wires=["control", "target"])
    qp.RY(x[1], wires="target")
    return qp.expval(qp.Z("target"))

print(circuit(params))
print(qp.draw(circuit)(params))
```

Use hashable custom wire labels when they improve readability. Avoid mixing integer wires with 0-d arrays; PennyLane treats them as different labels.

## Change device or execution settings

Use `QNode.update` when reusing the same quantum function with different settings:

```python
new_dev = qp.device("lightning.qubit", wires=2)
fast_circuit = circuit.update(device=new_dev, diff_method="best")
```

Before moving to `lightning.gpu` or hardware, prove the required plugin and accelerator environment. `default.qubit` is the safest CPU baseline.

## Finite shots and sampling

```python
dev = qp.device("default.qubit", wires=1)

@qp.qnode(dev, shots=1000)
def sampled(theta):
    qp.RX(theta, 0)
    return qp.counts(qp.Z(0), all_outcomes=True)

print(sampled(0.3))
```

If a QNode was created with analytic behavior but a task needs samples, use `qp.set_shots`:

```python
sampled_once = qp.set_shots(circuit, shots=1000)
```

Compare sampled results statistically; do not assert exact equality unless the circuit and measurement make deterministic outcomes.

## Return multiple measurements

```python
@qp.qnode(qp.device("default.qubit", wires=2))
def multi(theta):
    qp.RX(theta, 0)
    qp.CNOT([0, 1])
    return qp.expval(qp.Z(0)), qp.probs(wires=[0, 1])

exp_z, probs = multi(0.2)
```

Document each returned value separately. Mixed measurement tuples can have different dtypes and shapes.

## Draw the circuit

```python
print(qp.draw(circuit)(params))
```

For Matplotlib output:

```python
import matplotlib.pyplot as plt
fig, ax = qp.draw_mpl(circuit)(params)
plt.show()
```

Use drawing levels to explain transform pipelines. If the device-expanded diagram differs from user code, route transform questions to the operators/transforms sub-skill.

## Validate a device/plugin with the CLI

Start with help:

```bash
pl-device-test --help
```

Then run explicit checks only after the plugin package is installed:

```bash
pl-device-test --device plugin.device --shots 1000 --analytic False
```

Use `--skip-ops` if the plugin intentionally supports a restricted operation set. Record device kwargs explicitly with `--device-kwargs KEY=VAL` rather than relying on hidden configuration.
