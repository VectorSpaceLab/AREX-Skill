---
name: uniad
description: "Operate the UniAD repository for planning-oriented autonomous
  driving data preparation, configs, training/evaluation, checkpoints, and
  visualization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# UniAD repo skill

Use this skill when a task involves the OpenDriveLab UniAD repository, planning-oriented autonomous driving, nuScenes-based BEV perception/prediction/planning workflows, UniAD checkpoints, OpenMMLab configs, `projects.mmdet3d_plugin`, or UniAD train/eval/visualization scripts.

UniAD is not a normal installed Python distribution in this checkout. It is an OpenMMLab plugin rooted at `projects.mmdet3d_plugin`, with public workflows driven by config files and launcher scripts.

## Quick route map

| User intent | Read |
|---|---|
| Prepare or validate nuScenes, CAN bus, map extensions, info PKLs, or motion anchors | `sub-skills/data-preparation/SKILL.md` |
| Choose/edit a config, understand stage1 vs stage2, inspect model heads/classes, or debug plugin/model registry issues | `sub-skills/config-and-model-architecture/SKILL.md` |
| Build train/eval/SLURM commands, place checkpoints, plan GPU usage, resume runs, or reproduce metrics | `sub-skills/training-evaluation/SKILL.md` |
| Inspect `results.pkl`, render BEV/camera/video outputs, or debug visualization/log artifacts | `sub-skills/visualization-and-results/SKILL.md` |

## Start here for new environments

Read `references/installation.md` before giving install advice. The public v2.0 docs specify Python 3.9, Torch 2.0.1+cu118, `mmcv-full==1.6.1`, `mmdet==2.26.0`, `mmsegmentation==0.29.1`, `mmdet3d==1.0.0rc6`, then `requirements.txt`.

Minimal plugin check from a UniAD checkout:

```bash
PYTHONPATH="$(pwd)":$PYTHONPATH python - <<'PY'
import torch, mmcv, mmdet, mmseg, mmdet3d
print(torch.__version__, torch.version.cuda, torch.cuda.is_available())
print(mmcv.__version__, mmdet.__version__, mmseg.__version__, mmdet3d.__version__)
import projects.mmdet3d_plugin
print('UniAD plugin import ok')
PY
```

Use `scripts/check_uniad_environment.py` when you need a structured import/CUDA/config smoke check.

## Core workflow order

1. Verify the environment and plugin import.
2. Use `data-preparation` to confirm `data/nuscenes/`, `data/infos/`, and stage-2 motion anchors.
3. Use `config-and-model-architecture` to choose between BEVFormer, stage1 track/map, and stage2 E2E configs.
4. Use `training-evaluation` to render train/eval commands and check checkpoints/GPU expectations.
5. Use `visualization-and-results` only after evaluation has produced a result pickle or show directory.

## Repo-level references

- `references/repo-provenance.md` — source commit, branch, evidence paths, and refresh triggers.
- `references/repo-routing-metadata.json` — managed repo-skills-router metadata.
- `references/installation.md` — public runtime stack, plugin import model, and version caveats.
- `references/checkpoints-and-models.md` — stage flow, checkpoint names, and task ownership.
- `references/troubleshooting.md` — cross-cutting symptom-to-route triage.

## Bundled repo-level script

- `scripts/check_uniad_environment.py` — checks imports, CUDA availability, plugin import, and optionally parses the public configs. Run it from a UniAD checkout or pass `--repo-root`.

## Important constraints

- Do not claim full metric reproduction from import/config checks alone. Full reproduction requires the nuScenes data, CAN bus/map extensions, correct info PKLs, checkpoints, compatible CUDA/OpenMMLab packages, and enough GPUs/VRAM.
- Do not tell future agents to run original repo scripts as the only guidance. Use the bundled command builders and references in this skill to synthesize safe commands.
- The legacy Dockerfile targets older CUDA/Torch/OpenMMLab versions than the v2.0 docs; treat it as historical unless the user asks for legacy setup.
- UniAD training/evaluation is expensive. For exploratory triage, prefer layout validation, config parsing, command rendering, and tiny import/CUDA checks before launching jobs.
