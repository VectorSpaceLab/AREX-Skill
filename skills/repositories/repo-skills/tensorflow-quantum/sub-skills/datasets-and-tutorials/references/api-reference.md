# API Reference

Public TFQ docs frame the library around quantum data and hybrid quantum-classical models. This sub-skill owns the dataset loaders and the notebook recipes that repeatedly show up in the public tutorials.

## Dataset helpers

| Symbol | Signature | Return / semantics | Evidence |
|---|---|---|---|
| `tfq.datasets.excited_cluster_states` | `(qubits)` | Returns `(circuits, labels)`. For each input qubit it adds one excited cluster-state circuit with label `1`, then adds one unexcited reference circuit with label `-1`. The helper expects a list/tuple/ndarray of `cirq.GridQubit` objects and at least 3 qubits. The five-qubit smoke case returns 6 circuits and 6 labels. | Source code, source tests, and installed-package inspection |
| `tfq.datasets.tfi_chain` | `(qubits, boundary_condition='closed', data_dir=None)` | Returns `(resolved_circuits, labels, pauli_sums, addinfo)`. Supported spin counts are `[4, 8, 12, 16]`; supported boundary conditions are only `['closed']`. The dataset contains 81 datapoints. Labels are `0` for the ferromagnetic phase (`g < 1`), `1` for the critical point (`g == 1`), and `2` for the paramagnetic phase (`g > 1`). | Source code, source tests, and installed-package inspection |
| `tfq.datasets.xxz_chain` | `(qubits, boundary_condition='closed', data_dir=None)` | Returns `(resolved_circuits, labels, pauli_sums, addinfo)`. Supported spin counts are `[4, 8, 12, 16]`; supported boundary conditions are only `['closed']`. The dataset contains 76 datapoints. Labels are `0` for the critical metallic phase (`Delta <= 1`) and `1` for the insulating phase (`Delta > 1`). | Source code, source tests, and installed-package inspection |

## Spin-system metadata

`SpinSystemInfo` is the namedtuple returned in the fourth tuple slot by `tfi_chain` and `xxz_chain`.
It carries:
- `g`
- `gs`
- `gs_energy`
- `res_energy`
- `fidelity`
- `params`
- `var_circuit`

## Dataset download behavior

The spin-system dataset helpers use a package-internal downloader with a default cache base of `~/tfq-datasets` and a `spin_systems` cache subdirectory. They fetch a zip archive on first use unless it is already cached locally.

## Notebook recipe anchors

| Notebook | Reused APIs | Tiny lesson |
|---|---|---|
| `hello_many_worlds.ipynb` | `tfq.convert_to_tensor`, `tfq.from_tensor`, `tfq.layers.Expectation`, `tfq.layers.ControlledPQC`, `tfq.layers.AddCircuit` | Circuit tensors are `tf.string` tensors; `Expectation` can be run directly on a circuit tensor, or you can use `ControlledPQC` for classically controlled circuits. |
| `gradients.ipynb` | `tfq.layers.Expectation`, `tfq.layers.SampledExpectation`, `tfq.differentiators.ForwardDifference` | The same circuit can be evaluated analytically or with sampling, and the notebook compares exact vs sampled forward passes and gradients. |
| `noise.ipynb` | `tfq.layers.Sample(backend='noisy')`, `tfq.layers.SampledExpectation`, `tfq.layers.NoisyPQC` | Sampling and noisy hybrid models are both shown with tiny examples. |
| `qcnn.ipynb` | `tfq.convert_to_tensor`, `tfq.from_tensor`, `tfq.layers.AddCircuit`, `tfq.layers.PQC` | Convert circuits to tensors, prepend a cluster state, and feed the result into a PQC classifier. |
| `quantum_data.ipynb` | `tfq.layers.AddCircuit`, `tfq.resolve_parameters`, `tfq.layers.Expectation` | Build PQK-style feature circuits around classical data and evaluate expectation values on tiled operator tensors. |
| `quantum_reinforcement_learning.ipynb` | `tfq.layers.ControlledPQC` inside a custom re-uploading layer | Use a PQC-like policy network with classical inputs and action-weighted observables. |
| `research_tools.ipynb` | `tfq.layers.Sample().to_tensor()` | Sample a circuit into a tensor for downstream classical tooling. |

## Public test anchors

- The cluster-state tests check invalid-input errors and the five-qubit smoke case (`6` circuits, `6` labels).
- The spin-system tests check supported spin counts, boundary conditions, tuple lengths, tuple types, fidelity, energies, and parameter resolution.

## Notebook maintenance note

Whole-notebook validation is maintainer-only and is not the default runtime helper for this sub-skill. For tiny packaged checks, run `python scripts/tfq_smoke_check.py --quick --datasets` from the root `tensorflow-quantum` skill directory.
