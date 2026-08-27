---
name: solo
description: "Operate the SOLO repository's legacy PyTorch/MMDetection workflows
  for object detection and instance segmentation, including inference,
  data/configuration, model customization, training, and evaluation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# SOLO operating guide

Use this skill when a task mentions **SOLO**, **SOLOv2**, box-free instance
segmentation, or this repository's legacy `mmdet` APIs/configs. It describes the
PyTorch/MMDetection v1-era package at the pinned provenance revision; do not
silently substitute modern MMDetection 2/3 APIs.

## Route the task

- **Image/video-frame prediction, result interpretation, or saved overlays** →
  read [`sub-skills/inference/SKILL.md`](sub-skills/inference/SKILL.md).
- **COCO/VOC/Cityscapes/custom data, annotation validation, config paths, or
  pipeline changes** → read
  [`sub-skills/data-config/SKILL.md`](sub-skills/data-config/SKILL.md).
- **SOLO/SOLOv2 model choice, registries, heads, losses, NMS, custom modules,
  or compiled operators** → read
  [`sub-skills/model-configs/SKILL.md`](sub-skills/model-configs/SKILL.md).
- **Training, checkpoint evaluation, log analysis, robustness, or FLOPs** →
  read [`sub-skills/training-evaluation/SKILL.md`](sub-skills/training-evaluation/SKILL.md).

Cross-route tasks are normal: validate data/configuration first, then use the
model route, and use inference or evaluation only after a checkpoint and
backend have been validated.

## Install and verify

Use a fresh, isolated environment for this legacy package. Install the public
package and its documented build/runtime requirements using the selected
checkout's supported installation instructions; the runtime anchor is
`mmcv==0.2.16`, with a torch/torchvision pair and CUDA toolkit matched to the
extension build. Do not upgrade an existing working environment just to make
this old stack fit.

After installation, run:

From the generated skill root, run:

```bash
python scripts/collect_env.py
python -m pip check
```

Treat any missing `*_cuda`/Cython extension as a blocked backend, not as a
successful CPU installation. Read
[`references/installation-and-compatibility.md`](references/installation-and-compatibility.md)
for the compatibility ladder.

## Compatibility gate

Before changing code or launching a long command, establish:

1. Python is in the repository's documented legacy range (Python 3.5+; Python
   3.7/3.8 is the practical target for this revision).
2. PyTorch is compatible with the old implementation (the project documents
   PyTorch 1.1+ and says versions >=1.5 were not tested), `mmcv==0.2.16` is
   installed, and the package imports from the intended environment.
3. CUDA is available for GPU inference, training, DCN, and the custom NMS/ROI
   operators. A CPU import or CPU tensor check does **not** prove CUDA-kernel
   support. Read [`references/installation-and-compatibility.md`](references/installation-and-compatibility.md)
   before attempting a legacy extension build.
4. Config, checkpoint, dataset, and output paths are explicit. Do not assume a
   default dataset root, download weights implicitly, overwrite a checkpoint, or
   start distributed work from a single-process prompt.

The bundled diagnostic reports versions, import outcomes, CUDA visibility, and
extension import failures without downloading data or changing files. For
shared failure recovery, read
[`references/troubleshooting.md`](references/troubleshooting.md).

## Working conventions

- Treat Python config files as executable configuration. Inspect inherited
  values and the final `model`, `data`, `train_cfg`, and `test_cfg` before
  editing. Use the data/config route for schema and path checks.
- Keep checkpoint provenance with the config and exact package revision. Model
  zoo AP/FPS numbers are historical references, not guarantees for a changed
  backend, image scale, checkpoint, or evaluation split.
- Prefer a tiny local fixture, `--help`, config construction, or log parser
  check before a dataset-scale command. Never hide a missing optional package,
  missing compiled operator, or unavailable CUDA backend with a CPU claim.
- Use the bundled helpers only with explicit user paths. They are convenience
  wrappers, not replacements for the package's config and checkpoint semantics.
- Do not use the skill for the separate PaddlePaddle implementation, release or
  publishing operations, Slurm/cluster administration, or destructive source
  migration unless the user explicitly asks for those maintainer tasks.

## Evidence and limits

The runtime graph is distilled from the package source, public docs, configs,
demo intent, tools, and representative tests. Source provenance and the
verification boundary are recorded in
[`references/repo-provenance.md`](references/repo-provenance.md). CUDA/Cython
extensions, full COCO training/evaluation, webcam/display access, distributed
launchers, model downloads, and optional robustness packages require explicit
runtime resources and remain separate gates.
