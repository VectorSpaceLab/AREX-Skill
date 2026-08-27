---
name: vgen
description: "Route VGen video-generation workflows for text-to-video,
  image-to-video, DreamVideo customization, and InstructVideo reward
  fine-tuning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# VGen

Use this repo skill when a task concerns the VGen repository, its YAML-driven video generation launchers, or one of its named model families: ModelScope text-to-video, I2VGen-XL, VideoComposer-style conditioning, HiGen, TF-T2V, InstructVideo, DreamVideo, VideoLCM, or SR600.

Do **not** use this skill for generic Diffusers usage, ordinary image classification/detection/segmentation, unrelated video editing, or pure deployment tasks that do not involve VGen configs, checkpoints, data lists, or runtime modules.

## First checks

1. Read `references/repo-provenance.md` before deciding whether this skill is current for a checkout.
2. Confirm the task's workflow family and route to the smallest matching sub-skill.
3. Check the target YAML's `TASK_TYPE`; VGen dispatch is config-driven.
4. Validate prompt/data lists before a long GPU run.
5. Confirm CUDA, checkpoints, ffmpeg, and optional workflow dependencies are present.

A minimal preflight from this skill root:

```bash
python scripts/check_runtime.py --repo-root /path/to/VGen --require-cuda
python scripts/dispatch_config.py --repo-root /path/to/VGen --dry-run --cfg configs/t2v_infer.yaml
```

## Setup

A typical local setup is:

```bash
# install a CUDA-matched PyTorch wheel first, then the repo requirements
pip install -r requirements.txt
# InstructVideo reward fine-tuning also needs the extra list in configs/instructvideo/requirements.txt
pip install -r configs/instructvideo/requirements.txt
```

If you are matching the legacy README environment exactly, follow the repository README's Python 3.8 / Torch 1.12 CUDA notes instead of mixing package versions. No editable install is required; the bundled helpers assume the checkout itself is on disk and can be pointed to with `--repo-root`.

## Sub-skill routing

- `sub-skills/text-to-video/`: ModelScope T2V, HiGen, TF-T2V, VideoLCM, VideoComposer-style conditioning, SR600 upscaling, generic `train_net.py` / `inference.py` config dispatch, T2V dataset/model smoke helpers.
- `sub-skills/image-to-video/`: I2VGen-XL image-to-video inference, `image|||caption` input lists, person-specialized I2VGen config, Cog predictor and Gradio demo as optional/reference-only surfaces.
- `sub-skills/dreamvideo/`: DreamVideo subject learning, motion learning, joint subject+motion inference, adapter-key inspection, and DreamVideo metric calculation.
- `sub-skills/instructvideo/`: InstructVideo reward fine-tuning, HPSv2 reward setup, LoRA/base evaluation presets, and WebVid reward-list preparation.

## Shared references

- `references/overview.md`: route map, workflow families, included/excluded evidence, and shared helper index.
- `references/configuration.md`: `Config`, `TASK_TYPE`, registry dispatch, `_BASE`/`vldm_cfg` layering, and CLI override caveats.
- `references/data-formats.md`: prompt-only, path-caption, VideoComposer-style, DreamVideo metric, and InstructVideo list schemas.
- `references/troubleshooting.md`: cross-cutting CUDA, ffmpeg, OpenCV/NumPy, registry, checkpoint, and list-file failures.
- `references/repo-routing-metadata.json`: structured router metadata for managed repo-skill import.

## Shared scripts

- `scripts/check_runtime.py`: import, CUDA, ffmpeg, and heavy `tools` registration preflight.
- `scripts/dispatch_config.py`: safe dry-run or execution wrapper for VGen YAMLs.
- `scripts/inspect_list_file.py`: list-file validator for common VGen schemas.
- `scripts/dump_unet_key_sets.py`: root-level alias for the DreamVideo temporal/spatial UNet key exporter.

## Environment guidance

The README documents a legacy Python 3.8 / Torch 1.12 CUDA 11.3 setup and also expects `ffmpeg`. Current checkouts may need a modern CUDA PyTorch stack compatible with `xformers`, `open-clip-torch`, `fairscale`, `diffusers`, `transformers`, OpenCV, and reward extras such as `piq` and `scikit-image`. Treat CPU-only imports as insufficient for generation, customization, reward fine-tuning, and metric proof.

## Operating guardrails

- Prefer copied YAML edits for numeric, boolean, list, dict, and nested config changes; keep positional CLI overrides for string-safe paths.
- Do not run demo wrappers (`gradio_app.py`, `predict.py`) unless the user explicitly wants ModelScope/Gradio/Cog deployment and accepts network/deployment dependencies.
- Do not silently switch workflow families when checkpoints or list files are missing.
- Keep generated previews, run logs, model downloads, and review/test artifacts outside this runtime skill tree.
