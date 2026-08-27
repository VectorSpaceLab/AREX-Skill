# API Overview

Use this page to route a TFQ question to the right sub-skill without rereading the whole package.

## Public surface map

| TFQ surface | Typical use | Owner |
|---|---|---|
| `tfq.convert_to_tensor`, `tfq.from_tensor`, `tfq.get_expectation_op`, `tfq.get_sampled_expectation_op`, `tfq.get_sampling_op`, `tfq.get_state_op`, `tfq.get_unitary_op`, `tfq.append_circuit`, `tfq.resolve_parameters`, `tfq.padded_to_ragged`, `tfq.padded_to_ragged2d`, `tfq.noise.*`, `tfq.math.*`, `tfq.get_quantum_concurrent_op_mode`, `tfq.set_quantum_concurrent_op_mode`, `tfq.util.*` | Raw circuit tensors, execution ops, noisy execution, similarity helpers, and low-level utility questions | `tensor-ops-and-execution` |
| `tfq.layers.*` | Circuit wiring, readout layers, and quantum-classical Keras models | `keras-quantum-layers` |
| `tfq.differentiators.*`, `tfq.optimizers.*` | Gradients, finite-difference rules, custom differentiators, and tiny optimizer loops | `differentiation-and-optimizers` |
| `tfq.datasets.*` | Cluster-state helpers, spin-system datasets, and notebook-derived recipes | `datasets-and-tutorials` |

## Fast routing clues

- If the prompt names `Expectation`, `Sample`, `State`, `Unitary`, `PQC`, `ControlledPQC`, or the noisy layer families, start with `keras-quantum-layers`.
- If the prompt names `inner_product`, `fidelity`, `mps_1d_expectation`, `mps_1d_sample`, or `mps_1d_sampled_expectation`, stay in `tensor-ops-and-execution`.
- If the prompt names `ParameterShift`, `Adjoint`, `ForwardDifference`, `CentralDifference`, `LinearCombination`, `rotosolve_minimize`, or `spsa_minimize`, use `differentiation-and-optimizers`.
- If the prompt names `excited_cluster_states`, `tfi_chain`, `xxz_chain`, or a tutorial notebook recipe, use `datasets-and-tutorials`.

## Shared smoke helper

The bundled smoke helper is `scripts/tfq_smoke_check.py`. Use `--quick` for the smallest check, then add `--layers`, `--datasets`, `--differentiators`, or `--math` when you need a slightly deeper smoke.
