# Performance and Analysis Troubleshooting

## CuPy or Triton import fails

Symptoms:
- `ModuleNotFoundError: No module named 'cupy'`
- `ModuleNotFoundError: No module named 'triton'`
- CUDA device is unavailable even though the package imports

Actions:
1. Verify PyTorch CUDA first: `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"`.
2. Install a CuPy wheel matching the CUDA runtime family, such as `cupy-cuda12x` or `cupy-cuda11x`.
3. Install Triton `>=3.3.1` for Triton backend workflows.
4. Run `scripts/backend_smoke.py --json` before running a long benchmark.

## Triton backend shape or mode error

Symptoms:
- A Triton neuron rejects single-step input.
- The tensor has `[N, ...]` shape but the neuron expects a time-major sequence.
- The model works with `backend="torch"` but not `backend="triton"`.

Actions:
- Use `step_mode="m"` and feed `[T, N, ...]` tensors.
- Reset state between trials with `functional.reset_net`.
- Compare a tiny input with the `torch` backend before debugging custom Triton code.
- Route pure step-mode explanation back to `core-snn`.

## Precision request falls back or fails

Symptoms:
- `precision='fp16'` requested on CPU.
- `precision='fp8-torchao'` says `torchao` is missing or CUDA capability is too low.
- `precision='fp8-te'` says Transformer Engine is unavailable.

Actions:
- Inspect `build_capability_report(model, device, mode)` before conversion.
- Use `strictness="strict"` only when fallback must be fatal.
- Treat FP8 as optional until the selected package, device, and runtime smoke are proven.
- Call `prepare_model_for_precision` before constructing optimizers.

## Memory optimization fails or does less than expected

Symptoms:
- `dummy_input must be provided` for higher levels.
- The summary reports a lower `applied_level` than requested.
- Profiling is slow or splits fewer layers than expected.

Actions:
- Provide representative `dummy_input` for `level > 1` or profile-driven split search.
- Start with `profile="safe"` or `prefer="speed"` before `profile="memory"` or `"exhaustive"`.
- Read `MemOptSummary.notes`, `skipped_steps`, and `recommendation` before changing the model.
- Avoid expensive profiling in routine agent verification.

## Counters or energy estimates look wrong

Symptoms:
- `DispatchCounterMode(strict=True)` raises for an unregistered aten operation.
- FLOP/MAC/SynOp/AC counts differ from another paper or profiler.
- Energy values are interpreted as real hardware power.

Actions:
- Start with `strict=False` to skip unsupported operations, then tighten only when the missing rule matters.
- Use one representative forward and reset model state between independent runs.
- Treat `estimate_compute_energy` as a normalized comparison regime, not a direct measurement of device power.
- Record the chosen `ComputeEnergyCostConfig` preset when comparing reports.
