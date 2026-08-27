# Specialized open-system API reference

This reference collects the QuTiP APIs that are too specialized for the generic solver route.

## Environment classes

Environment classes live under `qutip.core.environment` and expose spectral-density, correlation-function, and power-spectrum methods.
Representative constructors include:

```python
BosonicEnvironment(T=None, tag=None)
DrudeLorentzEnvironment(T, lam, gamma, *, Nk=10, tag=None)
UnderDampedEnvironment(T, lam, gamma, w0, *, tag=None)
OhmicEnvironment(T, alpha, wc, s, *, tag=None)
LorentzianEnvironment(T, mu, gamma, W, omega0=None, *, Nk=10, tag=None)
```

Use them when the task is about modeling a bath before it becomes a solver call.

## HEOM surface

HEOM APIs live under `qutip.solver.heom`.
Important entry points include:

```python
HEOMSolver(H, bath, max_depth, *, odd_parity=False, options=None)
DrudeLorentzBath(Q, lam, gamma, T, Nk, combine=True, tag=None)
DrudeLorentzPadeBath(Q, lam, gamma, T, Nk, combine=True, tag=None)
UnderDampedBath(Q, lam, gamma, w0, T, Nk, combine=True, tag=None)
LorentzianBath(Q, gamma, w, mu, T, Nk, tag=None)
```

Always make `max_depth`, bath exponent count, and model dimension explicit before suggesting a run.

## PIQS surface

PIQS lives under `qutip.piqs.piqs`.
Representative entry points include:

```python
Dicke(N, hamiltonian=None, emission=0.0, dephasing=0.0, pumping=0.0,
      collective_emission=0.0, collective_dephasing=0.0,
      collective_pumping=0.0)
num_dicke_states(N)
num_dicke_ladders(N)
num_tls(nds)
jspin(N, op=None, basis='dicke')
dicke(N, j, m)
excited(N, basis='dicke')
ground(N, basis='dicke')
```

Use PIQS when the symmetry-reduced Dicke basis is central to the task.

## Non-Markovian and Bloch-Redfield routes

- `brmesolve` and Bloch-Redfield tensor helpers are solver-adjacent but usually need bath-model reasoning.
- `qutip.solver.nonmarkov.transfertensor.ttmsolve` handles transfer-tensor workflows.
- If the task is only a simple Lindblad evolution, switch back to `dynamics-and-solvers`.
