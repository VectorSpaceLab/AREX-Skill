# Transpiler workflows

## 1. Transpile against a backend or fake backend

```python
from qiskit import QuantumCircuit, transpile
from qiskit.providers.fake_provider import GenericBackendV2

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

backend = GenericBackendV2(num_qubits=2, seed=123)
tqc = transpile(qc, backend=backend, optimization_level=1)
```

Use a backend or fake backend when the task is really about hardware constraints, not just abstract circuit transformation.

## 2. Build a preset pass manager explicitly

```python
from qiskit.transpiler import generate_preset_pass_manager

pm = generate_preset_pass_manager(backend=backend, optimization_level=2)
compiled = pm.run(qc)
```

Use the preset pass-manager builder when you need to talk about stages, plugin names, or stage-specific overrides.

## 3. Tune topology, layout, and routing

- Pass a `Target` when you already know the exact device constraints.
- Pass a `CouplingMap` when you only need topology.
- Use `layout_method`, `routing_method`, `translation_method`, and `scheduling_method` to override the preset defaults.
- Use `seed_transpiler` when deterministic comparisons matter.

## 4. Check stage-level behavior

When a circuit unexpectedly changes, compare the output of different optimization levels or explicit stage methods. That is often the fastest way to find whether the issue is layout, routing, translation, optimization, or scheduling.

## 5. Common transpiler decisions

- Prefer `Target.from_configuration(...)` when you need a compact synthetic backend description.
- Prefer a fake backend when you want a realistic mix of basis gates, coupling, and backend defaults.
- Use `transpile()` for the simple one-off case and `generate_preset_pass_manager()` when the user wants more control over the pipeline.
