# Dynamics and solver workflows

## Solve a simple Schrödinger equation

```python
from qutip import basis, sigmax, sigmaz, sesolve

psi0 = basis(2, 0)
H = 0.5 * sigmax()
out = sesolve(H, psi0, [0, 0.1, 0.2], e_ops=[sigmaz()])
```

Use this when the user wants coherent evolution of a pure state.

## Solve a Lindblad master equation

```python
from qutip import basis, sigmax, sigmaz, sigmam, mesolve

rho0 = basis(2, 0)
H = 0.5 * sigmax()
c_ops = [0.1 * sigmam()]
out = mesolve(H, rho0, [0, 0.1, 0.2], c_ops, e_ops=[sigmaz()])
```

Use this when collapse operators or density matrices matter.

## Build and evaluate a time-dependent coefficient

```python
from qutip.core.coefficient import coefficient

coeff = coefficient('sin(w * t)', args={'w': 2.0})
print(coeff(0.25))
```

Use this when the task involves a string coefficient, runtime compilation, or reusable time dependence.

## Compute a steady state

```python
from qutip import sigmaz, sigmam, steadystate

A = sigmaz()
c_ops = [sigmam()]
rho_ss = steadystate(A, c_ops)
```

Use this when the task asks for a stationary density matrix instead of time evolution.

## Compare a trajectory helper against the serial path

```python
from qutip.solver.parallel import parallel_map, serial_map

values = list(range(5))
print(serial_map(lambda x: x * x, values))
print(parallel_map(lambda x: x * x, values, map_kw={"num_cpus": 1}))
```

Use this when you need to confirm that the helper-map API works even without optional extras.
