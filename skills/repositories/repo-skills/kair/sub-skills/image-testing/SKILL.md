---
name: image-testing
description: "Run KAIR image restoration inference and evaluation workflows for
  denoising, deblocking, single-image super-resolution, SwinIR, USRNet, face
  enhancement, and profiling caveats."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# KAIR Image Testing

Use this sub-skill when the task is to run, adapt, or debug KAIR **image** restoration testing/inference workflows: DnCNN/FDnCNN/FFDNet/IRCNN denoising, DnCNN3 deblocking, SRMD/DPSR/MSRResNet/RRDB/IMDN/USRNet image SR, SwinIR image tasks, GPEN face enhancement, model-zoo lookup, or lightweight profiling caveats.

Do not use this sub-skill for training, VRT/RVRT video restoration, or dataset/LMDB preparation. Route those to `image-training`, `video-restoration`, or `data-preparation` respectively.

## Operating workflow

1. Identify whether the requested entry point is argparse-based or hard-coded:
   - Use `scripts/build_image_test_command.py` for dry-run commands for `main_test_dncnn.py` and `main_test_swinir.py`.
   - Use `references/model-script-reference.md` for the distilled model-family to script/checkpoint/data mapping.
   - Use `references/image-testing-workflows.md` for command patterns, hard-coded-script editing guidance, output locations, metrics, SwinIR task recipes, face enhancement, and profiling caveats.
2. Resolve checkpoint names through the root model-zoo/download guidance before running networked downloads. SwinIR weights live under `model_zoo/swinir/`; most other image weights live directly under `model_zoo/`.
3. Before full inference, prefer safe parser checks such as `python main_test_dncnn.py --help`, `python main_test_swinir.py --help`, and root downloader `--help`. Full inference needs local images and checkpoints.
4. For failures, consult `references/troubleshooting.md` first, especially for missing weights, empty image folders, wrong channel/noise/scale selection, CPU-vs-CUDA behavior, SwinIR tiling, GPEN weights, and the face-enhancer `op` import-path quirk.

## Bundled files

- `references/image-testing-workflows.md` — practical recipes and editing guidance.
- `references/model-script-reference.md` — model family, script, checkpoint, and default data-route table.
- `references/troubleshooting.md` — owned failure modes for image testing.
- `scripts/build_image_test_command.py` — self-contained dry-run command builder; it imports no KAIR modules and never downloads or runs inference.
