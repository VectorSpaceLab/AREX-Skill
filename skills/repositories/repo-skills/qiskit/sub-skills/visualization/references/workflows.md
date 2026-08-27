# Visualization workflows

## 1. Draw circuits

```python
from qiskit import QuantumCircuit
from qiskit.visualization import circuit_drawer

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
text = circuit_drawer(qc, output="text")
fig = circuit_drawer(qc, output="mpl")
```

Use `output="text"` for terminal-friendly checks and `output="mpl"` for figure workflows. Use `filename=` or `fig.savefig(...)` when writing files.

## 2. Plot counts and distributions

```python
from qiskit.visualization import plot_histogram

counts = {"00": 50, "11": 50}
fig = plot_histogram(counts, title="Bell counts")
```

Use `number_to_keep`, `legend`, `color`, and `sort` when comparing multiple distributions.

## 3. Plot quantum states

Use state plots such as `plot_bloch_vector`, `plot_bloch_multivector`, `plot_state_city`, `plot_state_hinton`, `plot_state_paulivec`, and `plot_state_qsphere` when the input is a `Statevector`, `DensityMatrix`, or compatible array-like state object.

## 4. Visualize devices and layouts

Use device and layout functions for backend maps, error maps, coupling maps, and transpiled-circuit layouts. Route to the transpiler sub-skill first when the circuit has not been compiled against a target.

## 5. Style and file output

- Prefer explicit `output=` and `filename=` arguments instead of relying on user config.
- Use style dictionaries or style names only after confirming the style JSON path exists.
- Set a non-interactive Matplotlib backend, such as `Agg`, for headless automation.
