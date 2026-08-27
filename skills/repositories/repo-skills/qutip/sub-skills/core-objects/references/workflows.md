# Core object workflows

## Build a simple composite system

```python
from qutip import basis, qeye, sigmaz, tensor, ket2dm

psi = tensor(basis(2, 0), basis(2, 1))
rho = ket2dm(psi)
H = tensor(sigmaz(), qeye(2))
```

Use this pattern when the problem is about composing subsystems or checking tensor dimensions.

## Measure an observable

```python
from qutip import basis, sigmaz
from qutip.measurement import measurement_statistics_observable

ev, projectors, probabilities = measurement_statistics_observable(basis(2, 0), sigmaz())
```

Use this when the task is about the measurement basis, collapse probabilities, or state update rules.

## Compare states or channels

```python
from qutip import rand_dm, fidelity, tracedist

rho1 = rand_dm(4)
rho2 = rand_dm(4)
print(fidelity(rho1, rho2))
print(tracedist(rho1, rho2))
```

Use this when the user asks whether two states are close, orthogonal, or physically equivalent.

## Smoke-test a random object

```python
from qutip import rand_ket, rand_super

psi = rand_ket(4)
channel = rand_super(4)
```

Use this when you need a quick validity check for a helper, a plot, or a metric.
