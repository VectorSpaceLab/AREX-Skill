---
name: vad
description: "Provides self-contained operating guidance for the VAD
  autonomous-driving repository, including legacy environment setup,
  nuScenes/CAN-bus data preparation, model/plugin configuration, training,
  single-GPU evaluation, and prediction visualization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# VAD repository skill

Use this skill when working with VAD v1 or the bounded VADv2 additions: preparing nuScenes temporal annotations, understanding the VAD plugin/config graph, training or evaluating VAD, or inspecting rendered predictions.

## Route by task

- **Install prerequisites, prepare nuScenes/CAN-bus, generate temporal PKLs, or validate paths:** [data-preparation](sub-skills/data-preparation/SKILL.md).
- **Understand VAD/VADHead/transformers, custom registries, config families, stage-1/stage-2/e2e, or VADv2 boundaries:** [architecture-configuration](sub-skills/architecture-configuration/SKILL.md).
- **Train, resume, override configs, evaluate, format results, or reproduce released weights:** [training-evaluation](sub-skills/training-evaluation/SKILL.md).
- **Inspect result artifacts or render camera/LiDAR/map/trajectory predictions:** [visualization](sub-skills/visualization/SKILL.md).

## Operating order

1. Read [environment-and-verification.md](references/environment-and-verification.md) and [troubleshooting.md](references/troubleshooting.md).
2. Keep the repository's legacy dependency family together: Python 3.8-era PyTorch/CUDA, `mmcv-full==1.4.0`, `mmdet==2.14.0`, `mmsegmentation==0.14.1`, MMDetection3D `v0.17.1`, `timm`, and `nuscenes-devkit==1.1.9`. Use compatible builds for the target host rather than mixing modern OpenMMLab packages into these configs.
3. Validate data and config contracts before any expensive command. The bundled scripts are read-only and do not download data, build native operators, train, evaluate, or render.
4. Treat actual VAD model/plugin execution as CUDA and native-extension dependent. CPU imports or config parsing do not prove model-runtime support.
5. Record the exact config, checkpoint, normalization, data root, and output artifact for every experiment. Read [repo-provenance.md](references/repo-provenance.md) when checking whether this guidance matches a repository snapshot.

## Safe checks

From the generated skill tree, the following are safe preflights:

```bash
python scripts/check_environment.py
python sub-skills/data-preparation/scripts/check_data_layout.py --data-root DATA_ROOT --canbus-root CANBUS_PARENT
python sub-skills/architecture-configuration/scripts/check_config_contract.py CONFIG --check-plugin
python sub-skills/training-evaluation/scripts/check_training_contract.py CONFIG
python sub-skills/visualization/scripts/inspect_result_artifact.py RESULTS.pkl
```

Use the workflow sub-skills for the actual repository commands. Do not start full training/evaluation, download nuScenes/checkpoints, or run a renderer merely to test installation.

## Important caveats

- VAD uses custom temporal nuScenes info files and CAN-bus-derived fields; stock MMDetection3D info PKLs are not drop-in replacements.
- The project documentation recommends two-stage training and warns that distributed evaluation can produce inaccurate metrics; evaluate with one GPU and `--launcher none`.
- Released checkpoint reproduction requires the legacy `img_norm_cfg` (`mean=[103.530,116.280,123.675]`, `std=[1,1,1]`, `to_rgb=False`), not the newer setting shown in the current configs.
- Missing `ball_query_ext` or another `*_ext` is an environment/native-build block, not a model-config typo. Preserve that distinction in reports.
