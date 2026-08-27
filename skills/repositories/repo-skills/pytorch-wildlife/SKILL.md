---
name: pytorch-wildlife
description: "Use Pytorch-Wildlife for conservation AI workflows involving
  camera-trap and overhead image detection, wildlife classification, bioacoustic
  audio pipelines, result post-processing, video demos, and legacy fine-tuning
  data preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Pytorch-Wildlife

Use this skill when a task names Pytorch-Wildlife, `PytorchWildlife`,
MegaDetector, HerdNet, OWL, Deepfaune, passive-acoustic wildlife monitoring,
or the companion camera-trap fine-tuning modules. It is a router for the
versioned public package and its documented companion workflows; it is not a
replacement for model weights, datasets, or a project-specific experiment
plan.

## Start safely

Install the public distribution in an isolated Python environment. The source
metadata for this snapshot requires Python `>=3.10`:

```bash
python -m pip install PytorchWildlife
```

The package has a broad dependency surface, including PyTorch/TorchVision/
TorchAudio, `supervision==0.23.0`, `gradio>=6.15.1,<7`, Ultralytics, YOLOv5,
`timm`, Lightning, and audio packages for bioacoustics. For a CUDA install,
select a PyTorch wheel compatible with the host driver before installing the
package. Do not use a default pretrained constructor merely to test imports:
model constructors may download weights.

Verify the installation without model construction:

```bash
python -c "import PytorchWildlife; print(PytorchWildlife.__version__)"
```

If the import fails in a modern environment around legacy `yolov5` and
`pkg_resources`, read the cross-cutting [troubleshooting reference](references/troubleshooting.md)
before changing package versions.

## Route by user intent

- **Image detection and localization** — read
  [detection](sub-skills/detection/SKILL.md) for MegaDetector V5/V6, HerdNet,
  OWL, devices, thresholds, batches, local weights, and detection results.
- **Species or image classification** — read
  [classification](sub-skills/classification/SKILL.md) for pretrained/custom
  classifiers, Deepfaune, batch inputs, and detector-crop classification.
- **Audio and passive acoustics** — read
  [bioacoustics](sub-skills/bioacoustics/SKILL.md) for YAML configs, annotated
  windows, mel spectrograms, checkpoints, training/inference flags, and CSVs.
- **Data, output, video, or UI** — read
  [data-and-postprocessing](sub-skills/data-and-postprocessing/SKILL.md) for
  image-folder datasets, transforms, JSON/visual outputs, safe separation,
  video callbacks, and Gradio/Docker caveats.
- **User dataset adaptation or fine-tuning** — read
  [fine-tuning](sub-skills/fine-tuning/SKILL.md) for the legacy classification
  and detection companions, split design, YAML/CSV/YOLO preflight, and weight
  handoff. Do not start training by default.

For a multi-stage request, route each stage to its owner rather than copying
all model and output details into one plan. A common image pipeline is:
`detection` → `classification` (only animal crops) →
`data-and-postprocessing`. An audio pipeline is:
`bioacoustics` preparation → training or checkpoint inference → CSV review.

## Cross-cutting operating rules

1. Decide whether the task permits network access, model-weight downloads,
   GPU execution, external credentials, and writes before running a command.
2. Prefer explicit local `weights=` and explicit `device=` values for
   reproducible or offline work. CPU is a valid structural fallback, but a CPU
   check does not prove CUDA throughput or model behavior.
3. Validate image/audio paths, label/class mappings, config ranges, and output
   containment before expensive inference or training.
4. Preserve source files. Post-processing helpers write copies/outputs; keep
   generated outputs outside recursively scanned input directories.
5. Treat the companion fine-tuning directories as legacy/experimental and keep
   their environment and checkpoints separate from core package inference.
6. Do not launch Gradio, pull Docker images, download external datasets, or run
   long training as an implicit “smoke test.”

## Public package map

- `PytorchWildlife.models.detection`: image/localization wrappers and model
  families.
- `PytorchWildlife.models.classification`: pretrained and custom image
  classifiers.
- `PytorchWildlife.models.bioacoustics`: spectrogram classifiers and checkpoint
  loading.
- `PytorchWildlife.data`: image-folder datasets, transforms, and bioacoustic
  data/config/window/spectrogram helpers.
- `PytorchWildlife.utils`: video processing and detection/classification output
  serializers.

Use [installation and deployment](references/installation-and-deployment.md)
for prerequisites, CUDA/codec/container choices; [API boundaries](references/api-boundaries.md)
for verified cross-module contracts; and [troubleshooting](references/troubleshooting.md)
for import, dependency, weight, path, and backend failures. Read
[repository provenance](references/repo-provenance.md) before deciding whether
this skill matches a checkout or whether a refresh is needed.
