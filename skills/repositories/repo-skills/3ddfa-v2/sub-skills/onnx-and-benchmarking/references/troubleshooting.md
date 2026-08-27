# ONNX troubleshooting

## Missing `.onnx` files

- Symptom: the benchmark or ONNX demo complains about missing ONNX artifacts.
- Likely cause: the source checkpoints have not been converted yet.
- Recovery: let the ONNX wrapper auto-convert inside the checkout, or pre-run
  the conversion path from a writable checkout.

## `onnxruntime` provider issues

- Symptom: ONNX imports succeed, but the provider list is empty or incomplete.
- Likely cause: the wrong wheel was installed or the environment is damaged.
- Recovery: reinstall the CPU runtime wheel and re-run the import smoke.

## OpenMP warnings or slow timings

- Symptom: the benchmark prints warnings or varies wildly between runs.
- Likely cause: the thread count is not fixed, or the platform lacks the
  expected OpenMP library.
- Recovery: keep `OMP_NUM_THREADS` fixed, rerun the helper, and install `libomp`
  on macOS if needed.

## Timing interpretation mistakes

- Symptom: the latency numbers look larger than expected.
- Likely cause: the user compared warmup-inclusive runs to steady-state runs or
  changed the input/backbone without noting it.
- Recovery: compare the same input, the same config, and the same repeated count.
