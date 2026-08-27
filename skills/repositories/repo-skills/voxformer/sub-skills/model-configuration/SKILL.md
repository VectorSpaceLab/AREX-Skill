---
name: model-configuration
description: "Choose, inspect, validate, and safely adapt VoxFormer QPN,
  single-image, temporal, and deform3D configurations across the repository's
  two-stage SSC pipeline."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Model configuration

Use this route when an agent must select a VoxFormer preset, understand the
stage-1/stage-2 boundary, change temporal input or voxel geometry, or diagnose a
model/config import failure. The public presets are under
`projects/configs/voxformer/`; use [the catalog](references/config-catalog.md)
for the exact field-level matrix and [the runtime contracts](references/runtime-contracts.md)
before editing a config.

## Operating route

1. **Classify the request.** Select stage 1 (`qpn.py`) only for class-agnostic
   query proposals. Select stage 2 (`voxformer-S.py`, `voxformer-T.py`, or a
   matching `*_deform3D.py`) for 20-class semantic scene completion. Do not
   treat a stage-1 checkpoint as stage-2 query data.
2. **Choose the smallest public preset.** Use S for one image and T when the
   dataset is configured with four reference offsets plus the current image.
   Start from the corresponding standard preset unless the operator explicitly
   has the custom 3D attention extension ready. Deform3D changes the stage-2
   self-attention implementation; it is not a general replacement for S/T.
3. **Run the read-only preflight** from the repository root:

   ```bash
   python skills/disco/voxformer/sub-skills/model-configuration/scripts/validate_config.py --help
   python skills/disco/voxformer/sub-skills/model-configuration/scripts/validate_config.py projects/configs/voxformer/voxformer-T.py
   ```

   Add `--use-mmcv` only when the installed legacy stack is the environment
   being checked. The helper never writes, imports the project plugin, builds
   an extension, downloads weights, or launches training.
4. **Check the contracts.** Confirm that `plugin=True` and
   `plugin_dir='projects/mmdet3d_plugin/'` can register `VoxFormer`,
   `VoxFormerHead`, the transformer classes, and the SemanticKITTI dataset.
   Confirm the stage-specific `data.*.type`, `query_tag`, `labels_tag`, image
   count, proposal shape, target shape, and checkpoint paths. Use
   `../environment-and-installation/SKILL.md` for dependency/CUDA/custom-op
   readiness and `../dataset-preparation/SKILL.md` for generated files.
5. **Adapt coherently.** If changing a range, voxel size, BEV dimensions,
   camera count, temporal offsets, or attention family, update every coupled
   field listed in the catalog and then rerun the helper. Keep edits in a new
   config when reproducibility matters; do not silently mutate a public
   baseline.
6. **Hand off execution.** Once config, environment, and data preflights pass,
   route long-running commands, checkpoint loading, and metric execution to
   `../training-and-evaluation/SKILL.md`. This sub-skill does not start
   training or evaluation.

## Hard gates

- A stage-2 config must use `dataset_type='SemanticKittiDatasetStage2'`,
  `model.type='VoxFormer'`, a 20-class `VoxFormerHead`, and the matching query
  and label artifacts. A stage-1 config must use `SemanticKittiDatasetStage1`
  and `LMSCNet_SS` with two classes.
- Standard S/T and custom deform3D are separate routes. The deform3D source
  contains a placeholder `sys.path` line and a deliberate import guard in
  `multi_scale_deformable_attn_3D_custom_function.py`; report that caveat and
  route to environment repair or a standard config rather than hiding all
  configs behind it.
- A successful static config load is not proof of a runnable model. CUDA,
  MMCV/mmdetection3d native operators, project registry imports, data files,
  and the requested checkpoint remain separate gates.

## Scope boundaries

- Installation, version/ABI setup, CUDA toolchains, and custom extension build
  steps belong to `../environment-and-installation/SKILL.md`.
- SemanticKITTI downloads, preprocessing, labels, pseudo voxels, and query
  generation belong to `../dataset-preparation/SKILL.md`.
- Distributed launch, full training/test commands, checkpoint execution, and
  final metric runs belong to `../training-and-evaluation/SKILL.md`.
- This route covers the config/API contracts that those sibling routes need;
  it does not replace them.

## Bundled resources

- [references/config-catalog.md](references/config-catalog.md)
- [references/runtime-contracts.md](references/runtime-contracts.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/validate_config.py](scripts/validate_config.py)
