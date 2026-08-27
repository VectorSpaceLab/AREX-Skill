---
name: interfaces-and-monitoring
description: "Operate DreamCraft3D installation, Docker, Gradio, GPU memory, and
  safe environment triage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Interfaces and Monitoring

Use this sub-skill when a user needs safe operator guidance before or during a DreamCraft3D run: dependency/backend triage, Docker/NVIDIA container setup review, Gradio launch or watch behavior, GPU memory expectations, and non-mutating environment diagnostics.

## Read first

- For installation requirements, dependency variants, backend matrix, CUDA/Docker prerequisites, and memory guidance, read [references/install-and-backends.md](references/install-and-backends.md).
- For Gradio launch/watch behavior, `outputs-gradio`, stop/watchdog semantics, and Docker compose workflow, read [references/gradio-and-docker.md](references/gradio-and-docker.md).
- For failure triage across CUDA, PyTorch wheels, nvdiffrast, tiny-cuda-nn, nerfacc, Docker, and Gradio, read [references/troubleshooting.md](references/troubleshooting.md).
- For a safe local diagnostic that does not install packages, import heavy ML libraries, start training, download checkpoints, build images, or run containers, use [scripts/check_dreamcraft3d_environment.py](scripts/check_dreamcraft3d_environment.py).

## Route elsewhere

- Four-stage DreamCraft3D training, checkpoint chaining, and `launch.py --train/--validate/--test/--export` command construction belong to the `generation-pipeline` sub-skill.
- Reference-image preprocessing, `_rgba/_depth/_normal` sidecars, and Omnidata image preparation belong to the `image-preparation` sub-skill.
- Mesh export layout, output directory summaries, metrics, and progress-video utilities belong to the `export-and-evaluation` sub-skill.
- Optional Zero123++ multiview generation, DreamBooth/LoRA texture boosting, and model artifact planning belong to the `bootstrapped-texture` sub-skill.

## Safe operating protocol

1. Treat DreamCraft3D as a CUDA-first research checkout. The documented default path expects an NVIDIA GPU with at least 20GB VRAM, and the documented defaults were run on 40GB A100-class GPUs.
2. Before giving run instructions, check Python version, visible GPUs, CUDA/PyTorch compatibility, required repo-relative files, and local model artifacts when relevant.
3. Do not run host-level installs, Docker builds, container starts, native training, model downloads, or checkpoint conversions unless the user explicitly asks for that operation and accepts the cost/mutation risk.
4. Prefer diagnostics and concrete next actions: identify the missing file, binary, package family, GPU, VRAM, CUDA wheel variant, Docker component, or Gradio watcher symptom.

## Quick diagnostic

From a user's DreamCraft3D checkout, run:

```bash
python skills/disco/dreamcraft3d/sub-skills/interfaces-and-monitoring/scripts/check_dreamcraft3d_environment.py --repo-root .
```

For machine-readable output and local checkpoint checks:

```bash
python skills/disco/dreamcraft3d/sub-skills/interfaces-and-monitoring/scripts/check_dreamcraft3d_environment.py --repo-root . --json --check-model-paths
```

The diagnostic reports warnings for unavailable CUDA/Docker/model artifacts without trying to repair them. Use those warnings to decide whether to route the user to environment preparation, model-artifact planning, or stage-specific command construction.
