---
name: performance-and-analysis
description: "Use SpikingJelly CUDA/CuPy/Triton backends, FlexSN, precision
  conversion, memory optimization, op counting, and energy/profiling workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Performance and Analysis

Use this sub-skill when the task is about runtime backends, custom kernels, precision policy, memory optimization, profiling, operation counts, or energy-style analysis for SpikingJelly models.

## Route here for

- `torch`, `cupy`, and `triton` neuron backend selection and smoke checks.
- `cuda_kernel`: CuPy-backed CUDA utilities, auto-CUDA code generation, spike-linear helpers, and experimental fused IF/LIF-linear kernels.
- `triton_kernel`: predefined multi-step Triton neurons, surrogate kernels, compression helpers, FlexSN, and torch-to-Triton tooling.
- `precision`: `PrecisionConfig`, `prepare_model_for_precision`, `build_capability_report`, `validate_capability`, and precision report saving.
- `memopt`: `memory_optimization`, gradient checkpointing, spike compression, profile/level selection, and `MemOptSummary` interpretation.
- `op_counter`: `DispatchCounterMode`, `FunctionCounterMode`, FLOP/MAC/AC/SynOp counters, memory-access counters, and compute-energy estimators.
- `quantize.py` and backend-related capability checks when they support the above workflows.

## Do not handle here

- Core SNN state, `step_mode`, reset, neurons, layers, monitors, or surrogate-gradient concepts: route to [core-snn](../core-snn/).
- Neuromorphic dataset loading or preprocessing: route to [datasets](../datasets/).
- ANN-to-SNN recipe selection, calibration data, or converted-model semantics: route to [ann2snn](../ann2snn/).
- Model-zoo training, `train_classify`, distributed topology, or benchmark launch planning: route to [training-and-scaleout](../training-and-scaleout/).
- NIR/Lava/Lynxi exchange or deployment formats: route to [deployment-exchange](../deployment-exchange/).

## Read first

- [`references/backend-performance.md`](references/backend-performance.md)
- [`references/memory-precision-profiling.md`](references/memory-precision-profiling.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)

## Bundled scripts

- [`scripts/backend_smoke.py`](scripts/backend_smoke.py): tiny `LIFNode` forward smoke for `torch`, `cupy`, and `triton`, with graceful skips for unavailable optional backends.
- [`scripts/memory_precision_smoke.py`](scripts/memory_precision_smoke.py): safe CPU-oriented precision, capability-report, memory-optimization, and energy-counting probe.

## Operating workflow

1. Classify the request as backend selection, precision policy, memory optimization, or analysis/profiling.
2. Prove the target environment before promising backend behavior: check `torch`, `torch.cuda.is_available()`, `cupy`, `triton`, and any selected FP8 package.
3. For backend questions, start with `scripts/backend_smoke.py` and compare against the `torch` backend before blaming model logic.
4. For precision, call `prepare_model_for_precision(model, device, config)` before constructing the optimizer because modules may be replaced.
5. For memory optimization, provide `dummy_input` when requesting `level > 1` or when profiling needs real activation sizes; otherwise expect fallback to safer checkpoint-only behavior.
6. For op counting or energy comparison, run one representative forward under `DispatchCounterMode` or use `estimate_compute_energy`; do not present normalized counts as exact hardware power measurements.
7. Route dataset-dependent throughput, training-topology, or deployment-runtime questions to their owning sub-skill.

## Verified baseline

The prepared inspection environment verified imports for `spikingjelly.activation_based.precision`, `triton_kernel`, `memopt`, `op_counter`, and `cuda_kernel`; CUDA was visible on an A100 host; `cupy-cuda12x` and `triton==3.3.1` were installed; tiny `torch`/CuPy/Triton `LIFNode` forwards passed. Optional Transformer Engine FP8, TorchAO FP8 execution, Megatron Core LLM scale-out, and Lava runtime were not part of the verified minimum.
