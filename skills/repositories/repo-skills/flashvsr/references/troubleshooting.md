# FlashVSR Cross-Cutting Troubleshooting

Read this for failures that span setup and inference; use the nearest
sub-skill reference for detailed recovery.

## Import and backend

If `diffsynth` or a `FlashVSR*Pipeline` import fails, first confirm that the
intended distribution and Python interpreter are being used. A missing
`block_sparse_attn` module is a hard LCSA block: the Wan DiT imports it at
module import time and the official masked stream calls its CUDA function.
Rebuild the extension against the exact PyTorch/CUDA/compiler/SM combination
and rerun its import gate. `is_full_block=True` is not a reliable dense
fallback.

A CUDA-enabled torch wheel proves framework device access, not extension ABI or
kernel readiness. For `undefined symbol`, `invalid device function`, or loader
errors, check the torch ABI, CUDA toolkit, dynamic-library visibility, compiler,
and GPU compute capability as one profile; remove stale extension build output
only before a deliberate rebuild. A100 SM80 is the verified target profile.

## Version and asset consistency

Keep v1 and v1.1 assets atomic. Full needs the Wan VAE file; tiny and tiny-long
need the conditional decoder checkpoint. All routes need the streaming DiT,
matching LQ projection, and a positive context tensor. Use the bundled weight
checker before ModelManager and stop on Git LFS pointer text, zero-byte files,
unknown model detection, projection strict-load mismatch, or unexplained decoder
missing/unexpected keys.

## Geometry, frames, and outputs

Prepare RGB tensors at 4x source scale, crop to positive 128 multiples, and pass
the same `(H, W)` in the tensor and pipeline arguments. Require `F=8n+1` and
expect `F-4` output frames; do not rely on scalar 16-pixel rounding inside the
pipeline. For fewer frames, use the bundled validator before allocating a
model. If output duration matters, use preserve-all padding and trim repeated
tail frames explicitly.

For MP4 errors, validate the output conversion order (`[3,T,H,W]` to
`[T,H,W,3]`, denormalize, uint8), writable output parent, FFmpeg availability,
codec support, frame geometry, and FPS. A file's existence alone is not a
successful inference check.

## Memory and quality

Use tiny-long for GPU-memory pressure, full VAE tiling for full-route decode
pressure, smaller 128-aligned geometry, lower sparse ratio only after checking
quality, and valid temporal segmentation for very long clips. Tiny-long still
retains host input/output tensors. If detail aliases, restore official LCSA,
`sparse_ratio=2.0`, and `local_range=11` before experimenting. If color fixing
is ineffective, compare `color_fix=True/False` with matching tensor shapes and
instrument broad exception handling rather than assuming correction succeeded.
