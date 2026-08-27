---
name: video-restoration
description: "KAIR VRT and RVRT video restoration testing and training guidance
  for video super-resolution, deblurring, denoising, frame interpolation, and
  space-time SR."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# KAIR video restoration router

Use this sub-skill when the task is about KAIR VRT or RVRT video workflows:
video super-resolution, video deblurring, video denoising, video frame
interpolation, space-time video SR, VRT/RVRT task IDs, video tiling/OOM, VRT or
RVRT training configs, or RVRT custom CUDA extension failures.

Before giving commands, assume the user is in their own KAIR checkout and has
installed PyTorch plus KAIR's `requirement.txt` dependencies. Treat VRT/RVRT
full inference and training as CUDA-first workflows; RVRT's guided deformable
attention path requires a working CUDA-capable PyTorch build, `nvcc`, and
`ninja` for the custom extension.

## Read these bundled references

- `references/vrt-rvrt-task-reference.md` for the VRT `001`-`009` and RVRT
  `001`-`006` task namespaces, checkpoint names, default test folders, and
  training config paths.
- `references/video-restoration-workflows.md` for quick testing, custom-folder
  commands, training command patterns, data layout expectations, tile semantics,
  auto-download caveats, and metric/output behavior.
- `references/troubleshooting.md` when CUDA extension builds, missing weights,
  missing data, Vimeo preparation, DDP checkpoint/static-graph resumes,
  `num_workers`, or OOM are involved.
- `scripts/build_video_restoration_command.py` to print safe KAIR VRT/RVRT test
  commands without importing KAIR, downloading files, or launching inference.

## Route to siblings for non-owned work

- Route video dataset regrouping, LMDB creation, meta-info validation, and
  destructive preparation scripts to `../data-preparation/SKILL.md`.
- Route generic image restoration testing to `../image-testing/SKILL.md`.
- Route generic image training and non-video KAIR configs to
  `../image-training/SKILL.md`.
- Route shared checkpoint acquisition policy to the root model-zoo/download
  guidance when available; VRT/RVRT test scripts can auto-download missing
  weights and some testsets, so call that out before running them.

Do not ask future agents to inspect the original KAIR source or docs for these
workflows. The operational task tables, command patterns, caveats, and failure
modes are distilled into this sub-skill's bundled references.
