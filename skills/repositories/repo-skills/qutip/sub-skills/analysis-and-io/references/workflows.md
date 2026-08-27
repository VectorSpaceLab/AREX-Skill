# Analysis and I/O workflows

## Render a Hinton plot in a headless environment

```python
import matplotlib
matplotlib.use('Agg')
from qutip import rand_dm, hinton

fig, ax = hinton(rand_dm(4))
fig.savefig('hinton.png')
```

Use this for quick matrix visualization or a smoke check that Matplotlib is available.

## Build a Bloch sphere plot

```python
import matplotlib
matplotlib.use('Agg')
from qutip import basis, Bloch

b = Bloch()
b.add_states(basis(2, 0))
b.add_vectors([1, 0, 0])
b.render()
```

Use this for qubit-state, point, vector, line, or arc visualization.

## Compute a Wigner function

```python
import numpy as np
from qutip import basis, wigner

x = np.linspace(-3, 3, 51)
y = np.linspace(-3, 3, 51)
W = wigner(basis(8, 0), x, y)
```

Use this when the task asks for phase-space or quasi-probability analysis before plotting.

## Save and load QuTiP objects

```python
from qutip import basis, qsave, qload

psi = basis(2, 0)
qsave(psi, 'psi0')
psi_again = qload('psi0')
```

`qsave` appends `.qu`, so the file written above is `psi0.qu`.

## Capture an environment summary

```python
import qutip
qutip.about()
```

Use this when reporting reproducibility details or debugging import/runtime issues.
