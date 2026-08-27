# Compile and performance guidance

Kornia is strongest when operations stay on PyTorch tensors, especially for differentiable and batched GPU workflows. CPU single-image uint8 pipelines from OpenCV, Pillow, or Albumentations may be faster in their native regime; do not present a Kornia timing without naming the device, batch, dtype, and baseline regime.

## torch.compile maintenance rules

When modifying Kornia source for `torch.compile` or `torch._dynamo` compatibility:

1. Reproduce the graph break with `torch.compile(fn, fullgraph=True)` on the real user path.
2. Fix the underlying traceability issue rather than guarding with `torch.compiler.is_compiling()`.
3. Preserve eager behavior byte-for-byte for existing defaults unless a new opt-in mode is intentionally added.
4. Add or update a `test_dynamo` that exercises the real path, including parameter generation for augmentations.
5. Run the focused module tests and record the exact torch version/backend used.

Common genuine fixes include branchless `torch.where`, `torch._assert_async` for tensor validation, and removing fixed-loop early exits only when trailing iterations are provably no-ops.

## Benchmark rules

Use the public benchmark harnesses and public Kornia APIs. Every benchmark result should record:

- Date and git commit.
- Hardware and device.
- Python, PyTorch, Kornia, and baseline library versions.
- Batch size, image size, dtype, and whether `torch.compile` was used.
- Median timing with warmup and synchronized GPU measurement.
- Honest baseline regimes: Kornia/torchvision batched float tensors versus OpenCV/Albumentations/Pillow per-image uint8 CPU loops.

Representative benchmark families:

- Augmentation flagship: random transform class APIs with parameter sampling included.
- Geometry flagship: `warp_perspective`, `warp_affine`, `rotate`, `resize`, perspective transform solve.
- Filters flagship: Gaussian/Sobel/Laplacian/median/box/Canny comparisons.
- Feature benchmarks: matching and local-feature quality/performance metrics.

## When not to benchmark

Do not run full cross-library or GPU benchmarks as part of routine skill validation. Use smoke scripts for environment checks. Run benchmarks only when the task is a performance PR, a user asks for timing, or a change claims speedup/compile coverage.

## Interpreting results

- Kornia compiled GPU-batched warps can beat CPU OpenCV by large margins because they run in a different but important differentiable/batched regime.
- CPU single-image filtering/augmentation often favors OpenCV-backed libraries; this is expected and should be stated.
- `torch.compile` is not universally faster. Some convolution-bound or data-dependent augmentations can regress or fail to compile; measure before recommending compiled execution.
- CUDA illegal memory access during compiled warmup poisons the process. Stop the run and restart with the faulting op skipped or eager-only.
