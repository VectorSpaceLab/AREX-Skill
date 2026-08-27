# Neural Rendering Troubleshooting

## Missing ray datasets or trained assets

Symptoms: `FileNotFoundError` for `training_data.pkl`, `testing_data.pkl`,
trained Gaussian tensors, camera trajectories, or camera metadata.

Recovery:

1. Determine whether the user needs a full reproduction or a tiny shape test.
2. For full reproduction, request the documented datasets/weights and cache
   location before running. Some assets are external downloads.
3. For a tiny test, synthesize small rays, camera matrices, gaussian parameters,
   or image tensors and validate shapes without claiming paper-quality output.

## CUDA is required by the full script

Symptoms: `.cuda()` fails, `Torch not compiled with CUDA enabled`, or device
mismatch errors appear after moving only some tensors to CPU.

Recovery:

- For algorithm inspection, replace `.cuda()` and `device='cuda'` with an
  explicit device argument and run tiny CPU tensors.
- For real rendering, install a matching torch/CUDA wheel in an isolated
  environment and verify a tiny CUDA tensor allocation first.
- Do not use CPU success as evidence for CUDA performance or full native
  reproduction.

## Rendering runs out of memory

Symptoms: CUDA OOM, process killed, or extremely slow ray marching/splatting.

Recovery:

1. Estimate rough tensor scale with `scripts/estimate_render_memory.py`.
2. Reduce `H`, `W`, `nb_bins`, ray batch/chunk size, or gaussian count.
3. Render in chunks and write outputs incrementally.
4. Avoid keeping training activations during inference; use no-grad where
   appropriate in an adaptation.

## All points or rays project off screen

Symptoms: errors like `All projected points are off-screen`, blank render, or
NaN/Inf projection coordinates.

Likely causes: wrong camera-to-world/world-to-camera convention, near/far bounds,
scaled intrinsics, coordinate frame mismatch, or invalid gaussian covariance.

Recovery:

- Validate camera matrix shape and orientation before rendering.
- Check near/far clipping and scale intrinsics consistently with resized image
  dimensions.
- Start with one synthetic primitive or a tiny ray bundle at known coordinates.
- Clamp or reject non-finite covariance/projection values before alpha
  compositing.

## Output frame saving fails

Symptoms: save errors for `novel_views`, frame paths, or image directories.

Recovery:

- Create a scratch output directory before saving.
- Do not write generated frames inside the skill directory.
- For verification, validate tensor shapes and finite values before enabling
  image writes.

## Single-view reconstruction shapes do not match

Symptoms: UNet output channels mismatch gaussian parameter decoding, intrinsics
broadcasting fails, or source/target index sampling is inconsistent.

Recovery:

- Verify image tensor layout (`B,C,H,W`) and intrinsics for each batch.
- Check parent/child gaussian counts and parameter heads separately.
- Use a one-image synthetic batch before loading real datasets.
