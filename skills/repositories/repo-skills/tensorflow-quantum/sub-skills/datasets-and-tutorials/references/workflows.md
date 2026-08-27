# Workflows

## 1) Inspect the toy cluster dataset

Use this when the prompt asks what `excited_cluster_states` returns or how to reproduce the smallest cluster-state example.

```python
import cirq
import tensorflow_quantum as tfq

qubits = cirq.GridQubit.rect(1, 5)
circuits, labels = tfq.datasets.excited_cluster_states(qubits)

assert len(circuits) == 6
assert len(labels) == 6
assert labels[-1] == -1
```

Notes:
- Every excited circuit gets label `1`.
- The final circuit is the unexcited reference and gets label `-1`.
- The five-qubit case is a good tiny smoke because it is large enough to exercise the full helper but still easy to inspect.

## 2) Inspect a spin-system dataset tuple

Use this when the prompt asks about `tfi_chain`, `xxz_chain`, or the `SpinSystemInfo` fields.

```python
import cirq
import tensorflow_quantum as tfq

qubits = cirq.GridQubit.rect(4, 1)
circuits, labels, pauli_sums, addinfo = tfq.datasets.tfi_chain(qubits)

info = addinfo[10]
print(info.g)
print(info.gs_energy)
print(info.params)
resolved = cirq.resolve_parameters(info.var_circuit, info.params)
```

Switch `tfi_chain` to `xxz_chain` when the user wants the XXZ dataset instead.
That dataset has the same tuple shape and metadata pattern, but it contains 76 datapoints and uses the XXZ label semantics.

Download reminder:
- The first call may fetch a zip archive via the Keras downloader.
- If the network is unavailable and the archive is not cached, stop and report the download blocker instead of faking data.

## 3) Reproduce a notebook-style tensor round-trip

Use this when the prompt asks how to convert Cirq circuits into TFQ tensors, append a gate, and inspect the result without running the full notebook.

```python
import cirq
import tensorflow_quantum as tfq

q = cirq.GridQubit(0, 0)
circuit1 = cirq.Circuit(cirq.X(q))
circuit2 = cirq.Circuit(cirq.H(q))

input_tensor = tfq.convert_to_tensor([circuit1, circuit2])
output_tensor = tfq.layers.AddCircuit()(input_tensor, append=cirq.Circuit(cirq.Y(q)))
round_tripped = tfq.from_tensor(output_tensor)

assert len(round_tripped) == 2
```

This pattern mirrors the `hello_many_worlds` and `qcnn` tutorial cells.

## 4) Tiny tutorial recipe map

Use these as the first-place summary when someone asks for a tutorial-style example:

- `hello_many_worlds.ipynb`
  - `tfq.convert_to_tensor([circuit])`
  - `tfq.from_tensor(...)`
  - `tfq.layers.Expectation(...)`
  - `tfq.layers.ControlledPQC(...)`
  - `tfq.layers.AddCircuit(...)`
- `gradients.ipynb`
  - `tfq.layers.Expectation(...)` with `ForwardDifference`
  - `tfq.layers.SampledExpectation(...)` with `ForwardDifference`
  - compare exact and sampled outputs on the same circuit
- `noise.ipynb`
  - `tfq.layers.Sample(backend='noisy')`
  - `tfq.layers.SampledExpectation(...)`
  - `tfq.layers.NoisyPQC(...)`
- `qcnn.ipynb`
  - `tfq.layers.AddCircuit(..., prepend=cluster_state_circuit(...))`
  - `tfq.layers.PQC(...)` on the cluster-state data
- `quantum_data.ipynb`
  - `tfq.layers.AddCircuit(...)`
  - `tfq.resolve_parameters(...)`
  - `tfq.layers.Expectation(...)` on tiled operator tensors
- `quantum_reinforcement_learning.ipynb`
  - custom re-uploading PQC policy built around `tfq.layers.ControlledPQC(...)`
- `research_tools.ipynb`
  - `tfq.layers.Sample().to_tensor()` for sampling into a tensor

## 5) Notebook validation note

Whole-notebook execution is maintainer-only and not the default runtime path for this sub-skill. Use the packaged smoke helper and the tiny snippets above for normal routing.
