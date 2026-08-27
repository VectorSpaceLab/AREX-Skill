# Troubleshooting

## Fast recovery order

1. Start a fresh process with `TF_USE_LEGACY_KERAS=1` set **before** importing
   TensorFlow or TensorFlow Quantum.
2. From the root `tensorflow-quantum` skill directory, run the shared smoke helper `python scripts/tfq_smoke_check.py --quick`.
3. If the failure is layer-specific, compare it against the rows below.

## Common failures and fixes

| Symptom | Likely cause | Recovery |
|---|---|---|
| Import or layer creation breaks under Keras 3 / `tf_keras` mismatch | `TF_USE_LEGACY_KERAS=1` was not set early enough | Restart the process, export `TF_USE_LEGACY_KERAS=1` before Python starts, and rerun the smoke helper. |
| `Sample`, noisy `Expectation`, `SampledExpectation`, `NoisyPQC`, or `NoisyControlledPQC` complains about missing `repetitions` | Shot/trajectory count is required but missing or not positive | Pass a positive integer `repetitions` value. For noisy PQC variants, always provide it. |
| `NoisyPQC` or `NoisyControlledPQC` complains about `sample_based` | The noisy layer needs an explicit boolean mode | Pass `sample_based=True` or `sample_based=False`. Use `True` for bitstring-sampled estimates and `False` for trajectory-based expectation estimates. |
| `PQC` or `ControlledPQC` rejects `backend='noisy'` | The non-noisy PQC families do not accept the noisy backend selector | Switch to `NoisyPQC` or `NoisyControlledPQC`. If a custom backend is truly needed, use the non-noisy family that accepts it. |
| `Expectation` or `SampledExpectation` backend type errors mention `cirq.Sampler` or `cirq.sim.simulator.SimulatesExpectationValues` | The backend class does not match the layer's contract | Use a sampler for sample-based layers, an expectation-value simulator for analytic `Expectation`, or the native defaults when no custom backend is needed. |
| `SampledExpectation` rejects a final-state simulator | A `cirq.SimulatesFinalState` backend was passed where a sampler is required | Use `Expectation` instead, or switch to a backend that implements `cirq.Sampler`. |
| `ControlledPQC` or `NoisyControlledPQC` gives a shape or symbol mismatch | The control tensor does not match `layer.symbols` or the quantum input still contains symbols | Keep the first input symbol-free, and make the second input shape `[batch_size, n_symbols]` with columns ordered to match the layer symbols. |
| `symbol_names` errors mention duplicates or bad types | Symbol names are not unique strings or `sympy.Symbol` objects | Convert the names to unique strings or symbols before calling the layer. |
| `symbol_values` rank errors or batch-size errors | Parameter values are not rank 2 or do not match the circuit batch | Reshape to `[batch_size, n_symbols]`. If one circuit should be reused across many parameter rows, pass one circuit, not a longer circuit list. |
| `operators` rank or batch mismatch errors | Operator shape does not match the circuit batch contract | Use a single operator, a flat operator list, or a properly nested batch so the layer can tile or align them. |
| `AddCircuit` complains about `append` and `prepend` | Both sides were provided or neither side was provided | Pass exactly one of `append` or `prepend`. |
| `State` or `Unitary` outputs are awkward to compare | Ragged outputs are expected for these layers | Convert with `.to_tensor()` or `.to_list()` before comparing, and keep circuits tiny when inspecting these layers. |
| Notebook validation is slow or brittle | Whole-notebook execution is being treated as the default workflow | Keep notebook execution as maintainer-only evidence and use the shared smoke helper plus small layer checks by default. |

## Layer-specific reminders

- `Expectation` with `backend='noiseless'` does not need `repetitions`. If a
  caller supplies repetitions on the noiseless path, remove them or switch to a
  noisy path.
- `Sample` always needs `repetitions`.
- `State` accepts a final-state backend, but not every backend object is valid.
- `Unitary` has no backend knob, so backend-related failures usually mean the
  input circuit or symbol values are malformed.
- `PQC` and `ControlledPQC` manage trainable parameters internally. If the user
  wants manual parameter control, use the underlying readout layers instead.

## When to stop and escalate

If the layer contract itself seems to be missing a needed capability, route the
problem to the low-level tensor-ops-and-execution sub-skill or the
challenge-specific differentiation sub-skill instead of guessing at a workaround.
