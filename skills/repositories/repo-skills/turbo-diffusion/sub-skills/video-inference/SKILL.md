---
name: video-inference
description: "Build and validate one-shot TurboDiffusion Wan T2V/I2V inference
  commands without running models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TurboDiffusion video inference

Use this sub-skill when the task is to plan or review a **one-shot** TurboDiffusion video generation command for:

- Wan2.1 text-to-video (T2V) using a single DiT checkpoint.
- Wan2.2 image-to-video (I2V) using separate high-noise and low-noise DiT checkpoints.
- Prompt, image, model/checkpoint, quantization, attention, output-path, and no-download preflight decisions.

Do **not** use this sub-skill for interactive multi-turn generation; route that to `interactive-serving`. Route checkpoint conversion, quantization, rCM/SLA training, and checkpoint merging to `training-and-checkpoints`. Route CUDA extension, Sparse/SageSLA dependency, custom-op, and low-level acceleration failures to `acceleration-backends`.

## Read first

- [references/video-inference.md](references/video-inference.md) — one-shot T2V/I2V workflow, preflight checklist, and output validation.
- [references/cli-reference.md](references/cli-reference.md) — verified CLI flags and bundled command-builder options.
- [references/model-assets.md](references/model-assets.md) — model catalog, checkpoint roles, quantized/unquantized selection, and required asset checklist.
- [references/troubleshooting.md](references/troubleshooting.md) — failure matrix for quant flags, high/low I2V paths, adaptive resolution, attention backends, missing assets, output suffixes, and prompt quality.

## Bundled helpers

These helpers only render shell commands. They do not import TurboDiffusion, download assets, run models, train, convert checkpoints, or access credentials.

- [scripts/build_t2v_command.py](scripts/build_t2v_command.py) — render a Wan2.1 T2V command and catch common checkpoint/`--quant_linear` mistakes.
- [scripts/build_i2v_command.py](scripts/build_i2v_command.py) — render a Wan2.2 I2V command and catch high/low checkpoint swaps, image-path omissions, and quantization flag mistakes.

## Source-layout command quirk

TurboDiffusion's public one-shot scripts are usually launched from a source layout with helper packages such as `imaginaire`, `rcm`, `serve`, `SLA`, and `ops` importable from the inner `turbodiffusion` source directory. If a command fails with an import such as `No module named imaginaire`, add a public source-layout `PYTHONPATH` pointing at that inner source directory, for example `PYTHONPATH=turbodiffusion`, or run from an environment/layout where those helper packages are already importable.
