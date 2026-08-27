# Troubleshooting

## Dataset download and cache failures

The spin-system dataset helpers use a package-internal downloader with a default cache base of `~/tfq-datasets` and a `spin_systems` cache subdirectory.

What to do:
- If the dataset is not cached yet, allow the network fetch once.
- If the fetch fails because the network or the remote host is unavailable, stop and report the download blocker.
- If a local cache exists, pass an explicit `data_dir` that points to it and retry once.
- Do not invent synthetic data as a fallback for a missing download.

## Dataset input errors

| Symptom | Likely cause | Action |
|---|---|---|
| `qubits must be a list or np.ndarray` | `excited_cluster_states` got a string or other non-sequence | Pass a list, tuple, or ndarray of `cirq.GridQubit` objects. |
| `qubits must contain cirq.GridQubit only` | Wrong qubit type | Use `cirq.GridQubit.rect(...)` or convert to `cirq.GridQubit` first. |
| `Cluster state dataset must be defined on more than two qubits` | Input has 1 or 2 qubits | Use at least 3 qubits; the 5-qubit case is the smallest useful smoke. |
| `Supported number of spins are [4, 8, 12, 16]` | Unsupported spin count | Choose one of the supported 1D lengths. |
| `Supported boundary conditions are ['closed']` | Open or custom boundary condition | Keep `boundary_condition='closed'` for these loaders. |
| `qubits must be a one-dimensional list` | Nested qubit list | Flatten the input to a single list of `cirq.GridQubit`. |

## Notebook execution failures

- Whole-notebook execution is maintainer-only and not the default runtime workflow.
- If a notebook cell hangs, reduce it to the tiny workflow snippet in `references/workflows.md` and stop before a full notebook run.
- If a notebook-only import fails, treat it as an optional notebook dependency issue. Common notebook-side dependencies include `nbformat`, `nbclient`, `matplotlib`, and the other packages imported by the tutorial itself.

## Circuit / layer mismatch clues

| Symptom | Likely cause | Action |
|---|---|---|
| `tfq.convert_to_tensor` / `tfq.from_tensor` mismatch | Raw Cirq objects were passed downstream without converting to a TFQ tensor first | Convert the Cirq circuits or operators first, then inspect the result with `tfq.from_tensor`. |
| `AddCircuit` output looks wrong | Append/prepend circuit uses incompatible qubits or the batch shape does not match the notebook recipe | Match the notebook's `cirq.GridQubit` layout and batch size. |
| `Expectation`, `Sample`, or `SampledExpectation` shape errors | Symbol names, symbol values, or operator batch dimensions do not line up with the tutorial cell | Align the symbol order with the notebook recipe and re-check the tensor batch shape. |
| `PQC` / `ControlledPQC` errors | Circuit observables or control inputs do not match the notebook layout | Use the recipe in the matching tutorial; for deeper layer mechanics, hand off to `keras-quantum-layers`. |

## Escalation

- Tensor or backend detail beyond this level: `tensor-ops-and-execution`
- Keras layer internals beyond tutorial recipes: `keras-quantum-layers`
