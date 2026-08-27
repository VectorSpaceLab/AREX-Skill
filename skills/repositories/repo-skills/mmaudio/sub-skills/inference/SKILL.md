---
name: inference
description: "Operate MMAudio inference for text-to-audio, video-to-audio,
  experimental image-to-audio, the CLI demo, the Gradio UI, and programmatic
  generation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MMAudio Inference

Use this sub-skill when the task is to run, package, or diagnose MMAudio inference only.
It covers pretrained model selection, CLI demo usage, Gradio launch behavior, and
programmatic generation wiring.

## What this sub-skill covers
- `demo.py` for command-line text-to-audio and video-to-audio generation.
- `gradio_demo.py` for the browser UI, including the experimental image-to-audio tab.
- `mmaudio.eval_utils.generate`, `load_video`, `load_image`, and `make_video` for custom callers.
- `mmaudio.model.networks.get_my_mmaudio` and `MMAudio.update_seq_lengths` for duration-aware inference.
- Safe command construction for `demo.py` without executing the model.

## Route elsewhere
- Training, checkpointing, and DDP setup -> training sub-skill.
- Dataset or feature preparation -> data-preparation sub-skill.
- Batch evaluation or onset metrics -> evaluation sub-skill.

## Operating rules
1. Default to `large_44k_v2` unless a smaller model or 16 kHz output is explicitly needed.
2. For any duration change, update both `seq_cfg.duration` and `net.update_seq_lengths(...)` before generation.
3. For video jobs, trust the duration returned by `load_video(...)`; it truncates to the usable clip and sync coverage.
4. Use `--skip_video_composite` when the user only needs audio or when video reconstruction is unnecessary.
5. High-resolution inputs slow decode/encode work without improving quality; trim or re-encode instead of upscaling.
6. The Gradio script downloads and loads the model at import time, then exposes only its output directory for browser access.

## Start here
- [`references/cli-reference.md`](references/cli-reference.md)
- [`references/api-reference.md`](references/api-reference.md)
- [`references/gradio-interface.md`](references/gradio-interface.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)
- [`scripts/build_demo_command.py`](scripts/build_demo_command.py)

## Notes
- This subtree is self-contained runtime guidance. Do not send future agents back to the original repository docs.
- Evidence labels used to build this sub-skill: README.md, docs/MODELS.md, demo.py, gradio_demo.py, mmaudio/eval_utils.py, mmaudio/model/networks.py, mmaudio/model/sequence_config.py, mmaudio/utils/download_utils.py.
