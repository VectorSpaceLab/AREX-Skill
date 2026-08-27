# Checkpoints and stage flow

## Source evidence

This reference is distilled from `README.md`, `docs/INSTALL.md`, `docs/DATA_PREP.md`, and `docs/TRAIN_EVAL.md`.

## Placement rule

Place UniAD checkpoints in the repository-level `ckpts/` directory so the public configs and launcher examples resolve their relative paths without edits.

Example layout:

```text
ckpts/
├── bevformer_r101_dcn_24ep.pth
├── r101_dcn_fcos3d_pretrain.pth
├── uniad_base_track_map.pth
└── uniad_base_e2e.pth
```

## Public checkpoint map

| File | Main use | Notes |
| --- | --- | --- |
| `ckpts/r101_dcn_fcos3d_pretrain.pth` | BEVFormer baseline init | Used by `projects/configs/bevformer/base_bevformer.py` via `load_from` |
| `ckpts/bevformer_r101_dcn_24ep.pth` | Stage1 track/map initialization | Used by `projects/configs/stage1_track_map/base_track_map.py` via `load_from` |
| `ckpts/uniad_base_track_map.pth` | Stage1 evaluation smoke / Stage2 initialization | Published stage1 checkpoint and the parent checkpoint for stage2 training |
| `ckpts/uniad_base_e2e.pth` | Stage2 evaluation target | Published full-model checkpoint for the end-to-end workflow |

## Stage flow

1. **BEVFormer baseline**
   - Config: `projects/configs/bevformer/base_bevformer.py`
   - Init checkpoint: `ckpts/r101_dcn_fcos3d_pretrain.pth`
   - Public queue length: `4`

2. **Stage1 track/map**
   - Config: `projects/configs/stage1_track_map/base_track_map.py`
   - Init checkpoint: `ckpts/bevformer_r101_dcn_24ep.pth`
   - Public queue length: `5`
   - Source note: the config comments that lowering queue length to `3` reduces memory but can reduce tracking performance.

3. **Stage2 end-to-end**
   - Config: `projects/configs/stage2_e2e/base_e2e.py`
   - Init checkpoint: `ckpts/uniad_base_track_map.pth`
   - Public queue length: `3`

## Expected evaluation signals

### Stage1 smoke target

The documented stage1 evaluation example for `ckpts/uniad_base_track_map.pth` expects:

- `AMOTA 0.394`
- `AMOTP 1.316`
- `RECALL 0.484`

The source docs note that these values can shift slightly when evaluation is run with a GPU count other than 8.

### Stage2 reference target

The published stage2 table reports a full-model reference checkpoint with approximate targets for tracking, mapping, motion, occupancy, and planning. Use those numbers as release targets, not as a strict local pass/fail threshold when the data or launch topology differ.

## Initialization versus resuming

- `load_from` is the initialization checkpoint that the config uses before training.
- `--resume-from` is a resume checkpoint that should carry optimizer and scheduler state.
- For the stage1 and stage2 public configs, prefer the config's `load_from` field for parent-stage initialization and reserve `--resume-from` for interrupted training.
- For evaluation, pass the checkpoint as the second positional argument to `tools/test.py` or the bundled launcher wrapper.

## If a checkpoint is missing

- Missing BEVFormer or stage1 parent checkpoints usually means the `ckpts/` directory is incomplete.
- Missing stage2 evaluation checkpoints usually means the user has not downloaded the released full-model asset yet.
- If the desired fix is really a data-layout issue instead of a checkpoint issue, route that problem to the data-preparation sub-skill.
