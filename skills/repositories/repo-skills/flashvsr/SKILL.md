---
name: flashvsr
description: "Routes official FlashVSR diffusion-based streaming video
  super-resolution setup, model preparation, and CUDA inference for v1 and
  v1.1."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# FlashVSR

Use this repo skill when a task involves the official OpenImagingLab FlashVSR
implementation, `diffsynth` FlashVSR pipelines, one-step streaming video
super-resolution, Locality-Constrained Sparse Attention (LCSA), the
`block_sparse_attn` backend, v1/v1.1 model bundles, or A100-oriented inference.
It is an operating guide for inference, not a training, dataset, or third-party
ComfyUI skill.

## Route by task

- **Install, diagnose, or validate weights/backend:** read
  [setup-and-weights](sub-skills/setup-and-weights/SKILL.md). Use its read-only
  environment and weight checkers before loading checkpoints.
- **Prepare inputs or run a restoration job:** read
  [inference](sub-skills/inference/SKILL.md), then its API and workflow
  references. Choose full, tiny, or tiny-long deliberately.
- **Check whether this skill matches a changed checkout:** read
  [repo-provenance.md](references/repo-provenance.md) before refreshing.
- **Cross-cutting failures:** read
  [troubleshooting.md](references/troubleshooting.md), then the nearest
  sub-skill troubleshooting reference.

## Public runtime contract

FlashVSR is primarily a **4x** video restoration pipeline. The official
conditioning tensor is RGB bfloat16 in `[-1, 1]` with shape `[1, 3, F, H, W]`.
Prepare the source with bicubic 4x scaling, center-crop each spatial dimension
to a positive multiple of 128, and use a streaming frame count `F = 8n + 1`.
The expected model output is `[3, F-4, H, W]`; it is converted to RGB uint8
frames and encoded as an MP4 at the source FPS.

The LCSA backend is not optional for the official masked streaming path. Before
expensive inference, require:

```bash
python -c "from block_sparse_attn import block_sparse_attn_func; print('LCSA import OK')"
```

A CUDA-enabled PyTorch import alone is not sufficient. The target profile
verified for this skill is Python 3.11, PyTorch 2.6.0+cu124, CUDA 12.4, and
NVIDIA A100 SM80. Other GPUs or CPU execution are not equivalent verification.

## Version and route rules

- Prefer **v1.1** for new runs; keep all DiT, projection, decoder, and VAE files
  from one version-atomic model directory.
- Use **full** when the Wan VAE route fits memory; use `tiled=True` when full
  VAE decode is the bottleneck.
- Use **tiny** for ordinary clips with the conditional decoder.
- Use **tiny-long** when GPU input/output memory is the limiting factor; it
  keeps prepared LQ slices and decoded chunks on CPU, but total host memory can
  still grow with duration.
- Start with one step, `cfg_scale=1.0`, `if_buffer=True`, `kv_ratio=3.0`,
  `local_range=11`, `color_fix=True`, and a sparse ratio of 2.0. Recompute
  `topk_ratio = sparse_ratio * 768 * 1280 / (H * W)` for every geometry.

## Installation boundary

The generated skill is self-contained runtime guidance and safe diagnostics; it
never downloads weights or depends on the original checkout at runtime. Install
the public `diffsynth` package and its pinned CUDA requirements according to
[install.md](sub-skills/setup-and-weights/references/install.md), build
Block-Sparse-Attention separately, and package the version-matched projection,
TCDecoder, and positive-context support in the application that executes
inference. Do not treat third-party integrations as the official path.

## Verification boundary

Static API, geometry, frame-plan, weight-contract, and diagnostic-script checks
are complete. Native LCSA kernel, real checkpoint loading, full/tiny/tiny-long
GPU inference, OOM recovery, and MP4 reopen checks must remain explicitly
reported as native candidates until executed with real weights. Read the final
verification report under the configured test artifact directory for the exact
status; this production run does **not** import the skill into the managed
router.
