# ONNX and benchmarking workflows

## CPU latency workflow

```bash
python <skill-root>/sub-skills/onnx-and-benchmarking/scripts/run-latency.py \
  --repo-root <checkout> -- \
  -f <image-path> --onnx --repeated 1 --warmup true
```

This path reports face-detection, 3DMM regression, and reconstruction timing.

## CPU microbenchmark

```bash
python <skill-root>/sub-skills/onnx-and-benchmarking/scripts/run-speed-cpu.py \
  --repo-root <checkout>
```

This path runs a random input through `weights/mb1_120x120.onnx` and prints the
mean and standard deviation per inference.

## ONNX behavior

- `FaceBoxes_ONNX` converts `FaceBoxesProd.pth` to `FaceBoxesProd.onnx` if the
  ONNX file is absent.
- `TDDFA_ONNX` converts the selected checkpoint and BFM decoder if their ONNX
  files are absent.
- Generated ONNX artifacts are written next to their source assets in the
  checkout.

## Threading and runtime knobs

- `OMP_NUM_THREADS` controls the ONNX benchmark thread count.
- The demo path sets `KMP_DUPLICATE_LIB_OK=True` before the ONNX import.
- The default path is CPU ONNX Runtime; GPU provider coverage is outside the
  selected baseline.
