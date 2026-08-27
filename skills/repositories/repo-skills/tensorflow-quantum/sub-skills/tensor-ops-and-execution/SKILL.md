---
name: tensor-ops-and-execution
description: "Route TFQ tensor conversion, raw execution-op getters, backend
  choice, parameter resolution, noisy execution, math helpers, and util-helper
  questions here."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tensor Ops and Execution

Use this sub-skill when the user is working directly with TFQ tensors or raw
execution helpers:

- `tfq.convert_to_tensor` and `tfq.from_tensor`
- `tfq.get_expectation_op`, `tfq.get_sampled_expectation_op`,
  `tfq.get_sampling_op`, and `tfq.get_state_op`
- `tfq.get_unitary_op` / `tfq.core.ops.tfq_unitary_op.get_unitary_op`
- `tfq.append_circuit`, `tfq.resolve_parameters`
- `tfq.padded_to_ragged` and `tfq.padded_to_ragged2d`
- `tfq.noise.expectation`, `tfq.noise.sampled_expectation`, and
  `tfq.noise.samples`
- `tfq.math.inner_product`, `tfq.math.fidelity`,
  `tfq.math.mps_1d_expectation`, `tfq.math.mps_1d_sample`, and
  `tfq.math.mps_1d_sampled_expectation`
- `tfq.get_quantum_concurrent_op_mode` and `tfq.set_quantum_concurrent_op_mode`
- `tfq.util.get_supported_gates`, `tfq.util.get_supported_channels`,
  `tfq.util.get_circuit_symbols`, and `tfq.util.exponential`

Typical user prompts here ask how to:

- turn Cirq circuits or Pauli sums into TFQ tensors and back
- choose the right backend for expectation, sampling, state, or unitary ops
- resolve symbols or append circuits before execution
- understand tensor rank, batch-size, symbol, or operator mismatches
- decide between noiseless and noisy execution paths

Do not route here for Keras layer assembly, differentiators or optimizers,
or dataset/tutorial workflows.

For exact signatures and behavior, read `references/api-reference.md`.
For usage patterns, read `references/workflows.md`.
For error recovery, read `references/troubleshooting.md`.
