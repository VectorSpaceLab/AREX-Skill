---
name: inference-and-postprocessing
description: "Route BiRefNet image/video inference, mask saving, foreground
  refinement, and output validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# inference-and-postprocessing

Use this sub-skill for BiRefNet inference tasks that need:
- a Hugging Face load path or a local `.pth` checkpoint
- image or directory-based mask generation
- foreground refinement or matting-style exports
- comparison panels and practical output validation
- notebook-style video inference guidance

## Stay in scope

Use the bundled references and scripts when the task is about:
- loading BiRefNet weights for inference
- preparing `Resize` + `ToTensor` + ImageNet normalization
- running `birefnet(input)[-1].sigmoid()` in eval mode
- saving masks, foregrounds, or comparison images
- understanding native `inference.py` output layout

## Route elsewhere

- Model/backbone internals, patch helpers, or export mechanics → `../model-architecture/SKILL.md`
- Dataset layout or config defaults → `../configuration-and-data/SKILL.md`
- Training, evaluation, metrics, or checkpoint selection → `../training-and-evaluation/SKILL.md`

## Runtime entry points

- `references/inference-workflows.md`
- `references/video-workflows.md`
- `references/troubleshooting.md`
- `scripts/birefnet_image_infer.py`
- `scripts/birefnet_refine_smoke.py`

## Operating notes

1. Start with `--help` or `--dry-run`.
2. Pass `--repo-root` explicitly so imports stay anchored to the intended checkout.
3. Choose `--model-source local` for a checkpoint file or `--model-source hf` for hub weights.
4. Use `--device auto`, `cpu`, or `cuda` based on the available backend.
5. Keep `--foreground-refine` and `--save-comparison` enabled when you need matting-style outputs.
6. Local checkpoints should be cleaned with `check_state_dict` before loading; the helper does this for you.

## Recommended operating flow

1. Confirm whether the task is single image, directory, video, or repo-style dataset inference.
2. Run `scripts/birefnet_refine_smoke.py --device cpu` if the user only needs postprocessing/backend sanity before loading model weights.
3. Run `scripts/birefnet_image_infer.py --dry-run` with the intended image directory, output directory, model source, device, and resolution before a real inference run.
4. For local checkpoints, route persistent key or tensor-size mismatches to `../model-architecture/SKILL.md`.
5. For outputs that will be evaluated with BiRefNet metrics, preserve dataset/model directory names that `../training-and-evaluation/SKILL.md` expects.

## Done criteria

- The model source and required assets are explicit: Hugging Face repo/cache or local `.pth` checkpoint.
- The device, resolution, and CPU/CUDA/autocast limits are stated.
- The expected mask, foreground, and comparison output directories are known.
- Optional foreground refinement and video processing are separated from the core mask inference step.

## Output conventions

- Masks go to `masks/`
- Foreground/matting exports go to `foregrounds/`
- Comparison panels go to `comparisons/`
- Relative folder structure under `--input` is preserved
