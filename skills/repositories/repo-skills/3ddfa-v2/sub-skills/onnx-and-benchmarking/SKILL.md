---
name: "onnx-and-benchmarking"
description: "Use 3DDFA_V2 ONNX Runtime acceleration and CPU latency or speed
  benchmark workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# ONNX and benchmarking

Use this sub-skill when the task is about `--onnx`, ONNX conversion, CPU
latency, `OMP_NUM_THREADS`, `latency.py`, or `speed_cpu.py`.

## When to read

Read this sub-skill when the task asks to:

- Use ONNX Runtime instead of the PyTorch model path.
- Explain or prepare `TDDFA_ONNX` and `FaceBoxes_ONNX`.
- Run end-to-end latency timing on an image.
- Run the model-only CPU microbenchmark.
- Diagnose missing `.onnx` files, OpenMP/libomp issues, or unstable timings.

## Before running

1. Use `../setup-and-assets/` to build and verify the baseline checkout.
2. Check `../../references/model-assets.md` for which `.pth`, `.pkl`, and
   generated `.onnx` assets are involved.
3. Keep benchmark inputs and thread counts fixed when comparing numbers.

## Latency wrapper

The latency wrapper preserves the original `latency.py` CLI. Put original
arguments after `--`:

```bash
python <skill-root>/sub-skills/onnx-and-benchmarking/scripts/run-latency.py \
  --repo-root <checkout> -- \
  -f <image-path> --onnx --repeated 1 --warmup true
```

This reports face detection, 3DMM regression, and reconstruction timing.

## Speed wrapper

The speed wrapper preserves `speed_cpu.py`:

```bash
python <skill-root>/sub-skills/onnx-and-benchmarking/scripts/run-speed-cpu.py \
  --repo-root <checkout>
```

It runs a random input through `weights/mb1_120x120.onnx` and prints the mean
and standard deviation per inference.

## ONNX conversion behavior

- `FaceBoxes_ONNX` converts `FaceBoxesProd.pth` to `FaceBoxesProd.onnx` if the
  ONNX file is missing.
- `TDDFA_ONNX` converts the selected `.pth` checkpoint and the BFM decoder if
  the ONNX artifacts are missing.
- Conversion is CPU-safe but mutates the checkout by writing generated `.onnx`
  files.

## Thread and provider notes

- The repo sets `OMP_NUM_THREADS=4` in the ONNX demo paths.
- `KMP_DUPLICATE_LIB_OK=True` is set by the demo scripts before ONNX imports.
- CPU ONNX Runtime is the baseline. CUDA/other providers are outside the
  required verification scope.
- On macOS, the original README notes that `libomp` may be required.

## Troubleshooting

Read `references/troubleshooting.md` for ONNX-specific issues and
`../../references/troubleshooting.md` for shared setup failures.
