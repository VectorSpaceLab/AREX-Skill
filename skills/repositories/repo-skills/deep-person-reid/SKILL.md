---
name: deep-person-reid
description: "Route Torchreid deep-person-reid workflows for person
  re-identification training, evaluation, feature extraction, metrics,
  visualization, and model export."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# deep-person-reid / Torchreid

Use this repo skill when a task involves Torchreid (`torchreid`) or Kaiyang Zhou's deep-person-reid package for person re-identification (ReID). It is an operating graph for package use, not a maintainer-development guide.

## Use this skill for

- Training or evaluating image/video ReID models such as OSNet, OSNet-AIN, ResNet, MLFN, HACNN, PCB, or MobileNet variants.
- Building Torchreid data managers, custom datasets, samplers, losses, optimizers, schedulers, and `Engine.run(...)` plans.
- Extracting embeddings with `FeatureExtractor`, computing query/gallery distances, CMC/mAP, re-ranking, model complexity, ranked-result visualization, or activation maps.
- Exporting core Torchreid checkpoints toward ONNX, OpenVINO, or TFLite-style artifacts with explicit optional-dependency checks.
- Diagnosing install/import, dataset-layout, config, optional-backend, checkpoint, or export failures.

## Do not use this skill for

- General person ReID literature surveys with no Torchreid/deep-person-reid implementation need.
- DML, OSNet-AIN NAS, or PA-100K attribute-recognition project-local scripts unless a future extension bundles those projects; they are recorded as long-tail gaps rather than runtime routes here.
- Claims that CUDA, OpenVINO, TensorFlow, TFLite, or large-dataset training was verified unless the current task runs those checks.

## Install

From a fresh clone of the package, install the runtime dependencies and the local package itself:

```bash
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

If editable installation fails because build-time NumPy/Cython visibility is missing, install the needed build prerequisites first and retry with `--no-build-isolation`, then use [references/troubleshooting.md](references/troubleshooting.md) for the exact recovery steps.

Run the quick verification check after install:

```bash
python scripts/check_torchreid_env.py --model-name osnet_x0_25
```

## First checks

1. Confirm the package is installed in the task environment:

   ```python
   import torchreid
   print(torchreid.__version__)
   ```

2. Confirm PyTorch/torchvision match the intended backend. CPU is enough for API inspection and small smoke tests; CUDA is optional but practical for real training/evaluation.
3. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a particular checkout.
4. For package/module coverage and backend status, read [references/package-overview.md](references/package-overview.md).
5. For cross-cutting failures, start with [references/troubleshooting.md](references/troubleshooting.md).
6. To run a quick non-training package check, use [scripts/check_torchreid_env.py](scripts/check_torchreid_env.py).

## Route map

### Training, evaluation, data, and configs

Use [sub-skills/training-evaluation/SKILL.md](sub-skills/training-evaluation/SKILL.md) when the request names training, testing, data managers, datasets, config files, CLI-style command generation, split-log parsing, or dataset mean/std.

Typical triggers: `ImageDataManager`, `VideoDataManager`, `Engine.run`, `scripts/main.py`-style workflow, `test.evaluate True`, `visrank`, Market1501/DukeMTMC/MSMT/CUHK03/MARS layouts, `RandomIdentitySampler`, `train.lr_scheduler`, checkpoint resume/fine-tune.

### Feature extraction, models, metrics, and visualization

Use [sub-skills/feature-extraction/SKILL.md](sub-skills/feature-extraction/SKILL.md) when the request names embeddings, `FeatureExtractor`, model keys, checkpoint loading, distance matrices, CMC/mAP, re-ranking, model complexity, ranked-result visualizations, or activation maps.

Typical triggers: compare query/gallery images, compute cosine/euclidean distances, load local weights without downloads, `evaluate_rank`, `re_ranking`, `compute_model_complexity`, `return_featuremaps=True`.

### Model export and deployment artifacts

Use [sub-skills/model-export/SKILL.md](sub-skills/model-export/SKILL.md) when the request asks to export a trained core Torchreid checkpoint to ONNX, OpenVINO, or TFLite-style outputs.

Typical triggers: `--include onnx`, OpenVINO Model Optimizer, `openvino2tensorflow`, dynamic axes, opset choice, model-name inference, optional export dependency failures.

## Root operating rules

- Prefer local checkpoint paths and explicit model names. Avoid automatic pretrained downloads unless the user approves network access.
- Treat datasets as user-provided unless a specific dataset class has an automated download path and the user approves network access.
- Use bundled helper scripts for command planning and smoke checks; do not tell future agents to run source-repo scripts from an unavailable checkout.
- Keep CPU verification separate from CUDA claims. CPU import/model/feature checks do not prove multi-GPU training throughput.
- Use export extras only for requested export formats; the core skill does not install ONNX/OpenVINO/TensorFlow by default.
- If a task requires the excluded `projects/` workflows, either report the long-tail gap or extend the repo skill by bundling those project sources and verification cases first.
