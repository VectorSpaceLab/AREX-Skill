# UniAD data-preparation troubleshooting

Use this checklist when UniAD fails before training/evaluation can start, or when a user asks whether a nuScenes layout is ready.

## Fast triage commands

Validate full E2E readiness:

```bash
python skills/disco/uniad/sub-skills/data-preparation/scripts/check_uniad_data_layout.py \
  --uniad-root <UniAD repo root> --version v1.0 --stage e2e
```

Validate a mini smoke layout without requiring the stage-2 motion anchor:

```bash
python skills/disco/uniad/sub-skills/data-preparation/scripts/check_uniad_data_layout.py \
  --uniad-root <UniAD repo root> --version v1.0-mini --stage stage1
```

Render, but do not execute, the data-info conversion command:

```bash
python skills/disco/uniad/sub-skills/data-preparation/scripts/build_data_command.py \
  --uniad-root <UniAD repo root> --version v1.0
```

## Missing `data/nuscenes` subdirectories

Symptoms:

- `FileNotFoundError` for `samples/...`, `sweeps/...`, or a nuScenes metadata JSON table.
- The validator reports missing `samples`, `sweeps`, `v1.0-trainval`, `v1.0-test`, or `v1.0-mini`.
- The converter reports zero available scenes.

Fix:

1. Confirm the raw nuScenes archive was extracted or symlinked under `data/nuscenes/`.
2. For normal UniAD train/validation, ensure at least `samples/`, `sweeps/`, and `v1.0-trainval/` exist.
3. For actual test-set conversion/submission, also ensure `v1.0-test/` exists.
4. For mini experiments, use `v1.0-mini/` and pass `--version v1.0-mini` to the command builder/converter. Do not expect mini to reproduce full UniAD metrics.

## Missing CAN bus or maps

Symptoms:

- Converter errors from the nuScenes CAN bus API.
- Dataset construction fails while generating map labels or vectorized map samples.
- The validator reports missing `data/nuscenes/can_bus/` or `data/nuscenes/maps/`.

Fix:

1. Download the nuScenes CAN bus extension and place it at `data/nuscenes/can_bus/`.
2. Download the nuScenes map expansion package and place it at `data/nuscenes/maps/`.
3. Check for the four standard map names: `boston-seaport`, `singapore-hollandvillage`, `singapore-onenorth`, and `singapore-queenstown`.
4. Re-run the layout validator before moving to train/eval command construction.

## Missing temporal info PKLs

Symptoms:

- Config parsing succeeds but dataset construction cannot open `data/infos/nuscenes_infos_temporal_train.pkl` or `data/infos/nuscenes_infos_temporal_val.pkl`.
- The validator reports missing info files.
- `ann_file` in a config points to `data/infos/...` but that directory is empty.

Fix:

1. Prefer the off-the-shelf temporal PKLs when possible:
   - `data/infos/nuscenes_infos_temporal_train.pkl`
   - `data/infos/nuscenes_infos_temporal_val.pkl`
2. If generating locally, render the command with `build_data_command.py` and check that `--root-path`, `--canbus`, and `--out-dir` point to the intended locations.
3. Make sure conversion dependencies are installed in the UniAD runtime environment: nuScenes devkit, MMCV/OpenMMLab packages, NumPy, pyquaternion, shapely, and related requirements.
4. Expect full conversion to read many camera/lidar files and to take materially longer than a parser check.

## Missing `motion_anchor_infos_mode6.pkl`

Symptoms:

- Stage-2/E2E config or model construction fails around `anchor_info_path`.
- Error mentions `data/others/motion_anchor_infos_mode6.pkl` or `anchors_all`.
- BEVFormer/stage-1 workflows run, but stage-2 E2E fails before training/evaluation begins.

Fix:

1. Create the directory: `mkdir -p data/others`.
2. Download/copy `motion_anchor_infos_mode6.pkl` to `data/others/motion_anchor_infos_mode6.pkl`.
3. If the file is nonstandard, inspect that it is a pickle containing an `anchors_all` entry compatible with six motion anchors per group.
4. If the user is only running BEVFormer or stage-1 track/map, do not block on this file unless they requested E2E readiness.

## PKLs contain root paths but config still prepends `data_root`

Symptoms:

- File paths in errors contain duplicated path components such as `data/nuscenes/data/nuscenes/samples/...`.
- A generated temporal PKL was created with `--root-path ./data/nuscenes` or an absolute dataset root.
- The layout exists, but loaders still fail to locate camera/lidar files.

Fix:

1. Determine whether the PKL stores root-prefixed paths by running the validator with PKL scanning enabled.
2. If stored paths already include `data/nuscenes/` or an absolute root, set the active UniAD config's `data_root = ""` or normalize the PKL paths.
3. Keep `info_root` pointed at the actual directory containing the PKLs.
4. Re-test dataset construction after changing the path convention; do not change model architecture to solve a data-root mismatch.

## Network and download expectations

Symptoms:

- `wget` or browser downloads fail, stall, or fetch small HTML/authentication pages instead of large `.pkl`/dataset files.
- Raw nuScenes archives are missing after only downloading UniAD helper files.

Fix:

1. Treat raw nuScenes, CAN bus, and map files as separately licensed external assets. A user may need a nuScenes account and manual acceptance of terms.
2. Check downloaded file sizes; a tiny file where a large pickle/archive is expected usually means an authentication, redirect, quota, or network issue.
3. Retry downloads with a resumable tool such as `wget -c` or `aria2c` when appropriate.
4. Do not assume the data-info PKLs include raw sensor data; they only reference files that must already exist locally.

## `v1.0-mini` versus trainval/test confusion

Symptoms:

- The user has `v1.0-mini/` only but runs commands/configs intended for full trainval.
- The converter command was given `--version v1.0-trainval` and produced incorrect nested version names or failed.
- Evaluation expectations cite official full-set metrics while only mini data exists.

Fix:

1. For the UniAD wrapper-style converter, use `--version v1.0` for full data conversion or `--version v1.0-mini` for mini conversion.
2. Do not pass `v1.0-trainval` as the wrapper `--version`; the converter derives the underlying trainval/test split from `v1.0`.
3. Use mini only for smoke tests, path checks, and command validation. Route metric-reproduction expectations to `training-evaluation` after full data/checkpoint readiness is confirmed.
4. Remember that public configs default test evaluation to the validation PKL; a separate `nuscenes_infos_temporal_test.pkl` is only needed after config changes for actual test-set workflows.

## When to route elsewhere

- If the next question is "what command trains/evaluates this config?" route to `training-evaluation`.
- If the next question is "which config field or model head should I edit?" route to `config-and-model-architecture`.
- If the next question is "how do I visualize or inspect result pickles?" route to `visualization-and-results`.
