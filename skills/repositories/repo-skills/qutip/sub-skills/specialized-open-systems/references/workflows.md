# Specialized open-system workflows

## Evaluate a bath environment

```python
import numpy as np
from qutip.core.environment import DrudeLorentzEnvironment

env = DrudeLorentzEnvironment(T=1.0, lam=0.5, gamma=2.0)
w = np.array([0.5, 1.0, 2.0])
print(env.spectral_density(w))
```

Use this when the user first needs to validate a spectral density or correlation function.

## Build a PIQS Dicke-basis system

```python
from qutip.piqs.piqs import Dicke, jspin, num_dicke_states

N = 4
jx, jy, jz = jspin(N)
system = Dicke(N, hamiltonian=0.1 * jz, emission=0.01, dephasing=0.02)
L = system.liouvillian()
print(num_dicke_states(N), L.shape)
```

Use this when the user wants symmetry-reduced dynamics for many identical two-level systems.

## Create a small HEOM bath object

```python
from qutip import sigmaz
from qutip.solver.heom import DrudeLorentzBath

bath = DrudeLorentzBath(sigmaz(), lam=0.1, gamma=1.0, T=1.0, Nk=2)
print(len(bath.exponents))
```

Use this as a setup sanity check before suggesting an expensive HEOM solve.

## Route back to ordinary solvers

If the task only needs a Hamiltonian, collapse operators, and time list, use `dynamics-and-solvers` instead of this subskill.
