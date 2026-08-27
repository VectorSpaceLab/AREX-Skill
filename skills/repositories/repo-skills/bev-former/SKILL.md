---
name: bev-former
description: "Routes BEVFormer camera-only 3D detection workflows, from
  install/import and config inspection through nuScenes data prep, distributed
  training and evaluation, and log analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BEVFormer

Use this skill for the BEVFormer repository when the task mentions BEVFormer, BEVFormerV2, nuScenes camera-only 3D detection, BEV perception, or the `projects.mmdet3d_plugin` OpenMMLab plugin.

## Start here

- Read [model zoo and config map](references/model-zoo-and-configs.md) when you need a family overview or a config knob refresher.
- Run [the bundled environment checker](scripts/check_bevformer_environment.py) for a quick import/config/CUDA smoke from any working directory.
- Read [repository provenance](references/repo-provenance.md) if you need to know whether this skill matches the current checkout before using or refreshing it.
- Read [troubleshooting](references/troubleshooting.md) when setup, import, data, checkpoint, or runtime errors appear.

## Route map

### `installation-and-configs`
Use this route for:
- legacy OpenMMLab install and import checks
- plugin wiring, config inheritance, and config summaries
- BEVFormer vs BEVFormerV2 architecture questions
- model-family selection and BEV/temporal knob questions

Read [sub-skills/installation-and-configs/SKILL.md](sub-skills/installation-and-configs/SKILL.md) and run its bundled config inspector when you need a static summary.

### `dataset-preparation`
Use this route for:
- nuScenes raw tree validation
- CAN-bus expansion placement
- temporal `nuscenes_infos_temporal_*.pkl` generation or validation
- `data_root` / `ann_file` layout questions

Read [sub-skills/dataset-preparation/SKILL.md](sub-skills/dataset-preparation/SKILL.md) and run its bundled layout checker when you need missing-path diagnostics.

### `training-and-evaluation`
Use this route for:
- distributed training commands
- distributed evaluation commands
- FP16 command composition
- checkpoint, launcher, and work-dir questions
- warnings about `--eval`, `--format-only`, or multi-GPU eval behavior

Read [sub-skills/training-and-evaluation/SKILL.md](sub-skills/training-and-evaluation/SKILL.md) and use the command builders instead of hand-editing shell launchers.

### `analysis-and-utilities`
Use this route for:
- JSON or JSONL log summaries
- routing benchmark or visualization requests
- checkpoint utility caveats
- safe analysis helpers that do not train or mutate checkpoints

Read [sub-skills/analysis-and-utilities/SKILL.md](sub-skills/analysis-and-utilities/SKILL.md) and use the bundled log summarizer for small fixtures.

## Public prerequisites

- Python 3.8 is the documented baseline.
- The legacy stack documented by the repo uses torch 1.9.1+cu111, mmcv-full 1.4.0, mmdet 2.14.0, mmsegmentation 0.14.1, and mmdet3d 0.17.1.
- BEVFormer data workflows assume nuScenes plus the CAN-bus expansion.
- Training, evaluation, and visualization are checkpoint- and GPU-dependent; use the command builders and references first.

## Bundled helpers

- `scripts/check_bevformer_environment.py` — run this first when imports or config parsing look broken.
- `sub-skills/installation-and-configs/scripts/inspect_bevformer_config.py` — use for a deeper static config summary.
- `sub-skills/dataset-preparation/scripts/check_bevformer_nuscenes_layout.py` — use for missing-data-path diagnostics.
- `sub-skills/training-and-evaluation/scripts/bevformer_train_command.py` and `sub-skills/training-and-evaluation/scripts/bevformer_eval_command.py` — use for copyable train/eval commands.
- `sub-skills/analysis-and-utilities/scripts/summarize_bevformer_log.py` — use for tiny log summaries.

## Minimal smoke check

If you have a checkout on disk, pass it explicitly to the helper so the script does not depend on shell activation state:

```bash
python scripts/check_bevformer_environment.py --repo-root <checkout-root> --config projects/configs/bevformer/bevformer_tiny.py
```

For a V2 config, point `--config` at `projects/configs/bevformerv2/bevformerv2-r50-t1-base-24ep.py`.

## Before refresh

Compare the current checkout against [repository provenance](references/repo-provenance.md) before deciding whether to refresh this skill.
