---
name: mmaction2
description: "Use MMAction2 for video understanding inference, datasets/configs,
  training/evaluation, models, registries, and deployment planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMAction2 repo skill

Use this skill when a task involves MMAction2, the OpenMMLab video-understanding toolbox for action recognition, skeleton/audio/video-text workflows, temporal localization, spatio-temporal action detection, model zoo configs, training/testing, evaluation, or registry-backed customization.

## Start with the right sub-skill

- [`sub-skills/inference-and-demos/SKILL.md`](sub-skills/inference-and-demos/SKILL.md) — recognizer inference, `init_recognizer`, `inference_recognizer`, `ActionRecogInferencer`, `MMAction2Inferencer`, label maps, prediction dumps, visualization, and optional detector/pose-assisted demos.
- [`sub-skills/data-and-configs/SKILL.md`](sub-skills/data-and-configs/SKILL.md) — dataset annotation formats, `VideoDataset`/`RawframeDataset`/`PoseDataset`/`AVADataset`/`ActivityNetDataset`, transform pipelines, config inheritance, naming, and `--cfg-options` overrides.
- [`sub-skills/training-and-evaluation/SKILL.md`](sub-skills/training-and-evaluation/SKILL.md) — training, testing, work directories, checkpoints, resume, AMP, CPU/GPU/distributed/Slurm command planning, metrics, dumps, and offline result analysis.
- [`sub-skills/models-and-extension/SKILL.md`](sub-skills/models-and-extension/SKILL.md) — model families, model-index categories, MMAction2 registries, custom modules/datasets/pipelines, project-style extensions, export, publishing, and deployment caveats.

## Install and import baseline

Read [`references/environment-and-installation.md`](references/environment-and-installation.md) before diagnosing setup problems. The public baseline is:

```bash
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0rc4,<2.2.0"
pip install mmaction2
```

For source-based development or access to the full tool/config tree, install the user's chosen MMAction2 checkout in editable mode after installing compatible PyTorch, MMEngine, and MMCV. CPU mode is supported for many smoke checks and small workflows; CUDA is optional unless the user asks for GPU-scale training/inference or a backend-specific native case.

Minimal import check:

```python
import mmaction, mmcv, mmengine, torch
print(mmaction.__version__, mmcv.__version__, mmengine.__version__, torch.__version__)
```

Run [`scripts/check_mmaction2_environment.py`](scripts/check_mmaction2_environment.py) when the task starts with installation, optional dependencies, CUDA availability, or config parse uncertainty.

## Operating rules

1. Prefer config/API inspection and command previews before launching expensive video workloads, training, distributed jobs, checkpoint conversion, or dataset-scale preprocessing.
2. Pass `device="cpu"` explicitly on CPU-only hosts; several MMAction2 APIs default to CUDA-like devices.
3. Treat model aliases, remote checkpoints, dataset downloads, and pretrained-weight URLs as network actions. Ask before relying on them when the user did not already authorize network/download work.
4. Keep data/config issues separate from train/test failures: first validate annotation schema, `data_prefix`, pipeline decode type, class count, and config inheritance, then plan a training/test run.
5. For optional workflows, name the missing extra precisely: `mmdet`/`mmpose` for detector/pose-assisted demos, `openai-clip`/multimodal packages for some multimodal surfaces, ONNX/TorchServe packages for export/deployment helpers.
6. Do not claim that GPU, Slurm, deployment, or optional dependency flows are verified unless they were actually run in the user's current environment.

## Common task routing

| User task | Read |
| --- | --- |
| "Run recognition on a video" / "use MMAction2Inferencer" | `inference-and-demos` |
| "What does `pred_score` contain?" / "map top-k labels" | `inference-and-demos` API reference |
| "Prepare custom videos/rawframes/skeleton/AVA data" | `data-and-configs` |
| "Fix `--cfg-options` or config inheritance" | `data-and-configs` |
| "Preview a CPU/GPU train/test command" | `training-and-evaluation` command builder |
| "Resume training or dump test predictions" | `training-and-evaluation` |
| "Which model family/config should I use?" | `models-and-extension`, then `data-and-configs` if config editing is needed |
| "Register a custom backbone/head/dataset/transform" | `models-and-extension` |
| "Export/publish/convert a checkpoint" | `models-and-extension` export/deployment reference |
| "Is this generated skill current for my checkout?" | [`references/repo-provenance.md`](references/repo-provenance.md) |

## Shared references and helpers

- [`references/environment-and-installation.md`](references/environment-and-installation.md) — public installation modes, dependency variants, optional extras, and safe environment checks.
- [`references/troubleshooting.md`](references/troubleshooting.md) — cross-cutting import, dependency, backend, data/config, checkpoint, and optional-extra failures.
- [`references/repo-provenance.md`](references/repo-provenance.md) — source snapshot used to generate this skill; read it before deciding whether to refresh the skill.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) — structured scenario metadata for managed repo-skill routing.
- [`scripts/check_mmaction2_environment.py`](scripts/check_mmaction2_environment.py) — safe import/version/backend/config probe.
