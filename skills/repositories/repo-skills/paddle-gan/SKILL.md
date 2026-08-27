---
name: paddle-gan
description: "Route PaddleGAN tasks to focused workflows for setup, data,
  training, media applications, and deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaddleGAN

Use this root only to check shared readiness and select a leaf workflow. Keep task-specific work in the selected leaf.

## First checks

1. Read [install and setup](references/install-and-setup.md), choose a CPU or CUDA-enabled Paddle build, and install `ppgan` in the environment that will run the task.
2. Run [the install checker](scripts/check_install.py); require GPU, ffmpeg, face, or CLIP support only when the requested workflow needs it.
3. For YAML-driven work, parse the config and overrides with [the config checker](scripts/check_config.py) before training or export.
4. If a check fails, use [shared troubleshooting](references/troubleshooting.md) before entering a leaf.

## Route exactly one primary task

| Primary intent | Route |
| --- | --- |
| Train, evaluate, resume/load a checkpoint, inspect YAML, AMP, VisualDL, or distributed launch | [training-configs](sub-skills/training-configs/SKILL.md) |
| Run a single-image, face, portrait, latent, restoration, style, or `ppgan.apps` image predictor workflow | [image-and-face-apps](sub-skills/image-and-face-apps/SKILL.md) |
| Process video/audio, motion transfer, interpolation, video restoration/SR, First Order Motion, or Wav2Lip | [video-and-audio-apps](sub-skills/video-and-audio-apps/SKILL.md) |
| Prepare, download, preprocess, or validate dataset folders and `dataroot` values | [data-preparation](sub-skills/data-preparation/SKILL.md) |
| Export checkpoints, inspect static artifacts, or plan Paddle Inference, TensorRT, Serving, Lite, C++, or TIPC work | [deployment-export](sub-skills/deployment-export/SKILL.md) |

Use the [workflow map](references/workflow-map.md) for model-family routing and mixed requests.

## Cross-workflow sequence

Route each stage separately: shared readiness → data preparation (if data changes) → training or app inference → deployment/export (only if a static/runtime artifact is requested). A model name does not override the stage: for example, Wav2Lip corpus preparation routes to data preparation, Wav2Lip media inference routes to video/audio, and Wav2Lip checkpoint export routes to deployment/export.

Do not run downloads, full training, heavy media inference, compilation, or deployment services merely to route a request.

## Provenance and router metadata

- [Repository provenance](references/repo-provenance.md) records the versioned evidence baseline and refresh checklist.
- [Routing metadata](references/repo-routing-metadata.json) is the machine-readable `repo-skills-router` entry for discovery.

