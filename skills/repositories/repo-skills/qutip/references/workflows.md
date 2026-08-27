# Common QuTiP workflows

These are short, representative workflows that show how the subskills fit together.
Each example is intentionally small so you can adapt it to a real problem.

## 1) Build and inspect quantum objects

```python
from qutip import basis, qeye, destroy, tensor, ket2dm, sigmaz

psi = tensor(basis(2, 0), basis(2, 1))
rho = ket2dm(psi)
H = tensor(sigmaz(), qeye(2)) + tensor(qeye(2), destroy(2).dag() * destroy(2))
```

Use `core-objects` when you need to check dimensions, tensor structure, Hermiticity, or measurement compatibility.

## 2) Evolve a state with a solver

```python
from qutip import basis, sigmax, sigmaz, mesolve

psi0 = basis(2, 0)
H = 0.5 * sigmax()
out = mesolve(H, psi0, [0, 0.1, 0.2], [], e_ops=[sigmaz()])
```

Use `dynamics-and-solvers` when the task is about choosing the solver, adding collapse operators, configuring `QobjEvo`, or handling time-dependent coefficients.

## 3) Solve a specialized open-system model

```python
from qutip.core.environment import DrudeLorentzEnvironment
from qutip.piqs.piqs import num_dicke_states

env = DrudeLorentzEnvironment(T=1.0, lam=0.5, gamma=2.0)
print(num_dicke_states(4))
print(env.spectral_density([0.5, 1.0, 2.0]))
```

Use `specialized-open-systems` when the task names PIQS, HEOM, non-Markovian transfer-tensor methods, or an environment model.

## 4) Visualize and save results

```python
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
from qutip import basis, rand_dm, hinton, Bloch, qsave, qload

rho = rand_dm(4)
fig, ax = hinton(rho)
fig.clf()

qubit = basis(2, 0)
b = Bloch()
b.add_states(qubit)
b.render()

path = Path('state')
qsave(qubit, path)
loaded = qload(path)
```

Use `analysis-and-io` when the task is about plotting, serialization, tomography, notebook helpers, or citation/environment summaries.

## Best practice checklist

- Start with the simplest object and solver that matches the physics.
- Use `qutip.about()` and `qutip.settings` to diagnose environment behavior.
- In headless environments, set the Matplotlib backend before importing plotting helpers.
- Keep temporary save/load and plotting checks inside a scratch directory.
