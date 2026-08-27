---
name: inference-pipelines
description: "Helps agents select LTX-2 inference pipelines, build safe
  CLI/Python invocation plans, choose checkpoint layouts, and diagnose
  conditioning, HDR, retake, audio, Dub-It, and DFR generation issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# LTX-2 inference pipelines

Use this sub-skill when the user needs to choose or prepare an LTX-2 inference pipeline for text-to-video, image-to-video, video-to-video IC-LoRA, keyframe interpolation, audio-to-video, retake, HDR/EXR, Dub-It, text-to-audio, or DFR detail-fidelity rendering. It is for building correct commands and Python calls, validating local asset layouts, and troubleshooting before a generation run.

Do not use this sub-skill for low-level tensor/model construction, package installation, accelerator tuning, dataset work, or training. Route those requests to the sibling sub-skills named in [Routes](#routes-to-sibling-sub-skills).

## Fast workflow

1. Identify the requested conditioning source and output type, then choose a pipeline with [pipeline-selection.md](references/pipeline-selection.md).
2. Decide the checkpoint layout: LTX-2.5 split components or LTX-2.3/legacy monolith. Use [cli-reference.md](references/cli-reference.md) for required flags and recipes.
3. Validate prompt, frame count, dimensions, input media, and HDR/EXR rules with [conditioning-and-hdr.md](references/conditioning-and-hdr.md).
4. For programmatic use, map the choice to the public class and signatures in [python-api.md](references/python-api.md).
5. If preparing a command without running generation, use the bundled helpers:
   - [scripts/inspect_pipeline_cli.py](scripts/inspect_pipeline_cli.py) prints or runs `--help` for known `ltx_pipelines` modules.
   - [scripts/build_distilled_command.py](scripts/build_distilled_command.py) builds a safe LTX-2.5 split `DistilledPipeline` command and validates local asset paths by default.
6. If a planned run fails or looks risky, diagnose with [troubleshooting.md](references/troubleshooting.md).

## Public runtime safety

- The references here are self-contained distilled operating knowledge. Do not open original repository docs, examples, tests, or source scripts during normal runtime use.
- The bundled scripts are inspection/build helpers only. They do not download models, train, generate video/audio, use credentials, contact the network, or delete user data.
- Always use local model and media paths supplied by the user. Avoid commands that implicitly download checkpoints.

## Routes to sibling sub-skills

- **core-components**: custom model builders, schedulers, denoisers, VAE internals, tensor shapes, latent/state components, or hand-authored diffusion loops.
- **performance-backends**: installation, CUDA/ROCm/MPS setup, optional NATTEN/FlashAttention/DiffVAE backends, quantization tradeoffs, compile tuning, multi-GPU execution, or memory benchmarking. This sub-skill only names the relevant inference flags.
- **data-preparation**: media/dataset preprocessing, caption manifests, training datasets, or batch asset conversion.
- **training-workflows**: LoRA/full training, IC-LoRA training, trainer config files, or checkpoint export.
