# VAD data contract

## When to read

Read this before preparing data, changing `data_root`, or explaining why a VAD config cannot find its annotations. Facts are distilled from the repository's installation/data preparation documentation, converter, VAD dataset, and VAD configs.

## Dependencies and external inputs

The documented stack is an older OpenMMLab release family: Python 3.8-era PyTorch/CUDA, `mmcv-full==1.4.0`, `mmdet==2.14.0`, `mmsegmentation==0.14.1`, MMDetection3D `v0.17.1`, `timm`, and `nuscenes-devkit==1.1.9`. Match compatible wheels/builds for the target host; do not blindly mix modern OpenMMLab releases with these configs.

You need:

- nuScenes v1.0 data (`maps`, `samples`, `sweeps`, and the relevant `v1.0-trainval` or `v1.0-test` metadata directory).
- The CAN-bus expansion, normally exposed below a separate CAN-bus parent containing `can_bus/`.
- Enough storage and permissions for the raw data and generated PKLs.

## Expected layout

A typical layout is:

```text
DATA_ROOT/
  maps/
  samples/
  sweeps/
  v1.0-trainval/
  vad_nuscenes_infos_temporal_train.pkl
  vad_nuscenes_infos_temporal_val.pkl
  nuscenes_map_anns_val.json        # required by the validation config
CANBUS_ROOT/
  can_bus/
```

The VAD configs use `data/nuscenes/` as a relative default and refer to:

- `vad_nuscenes_infos_temporal_train.pkl`
- `vad_nuscenes_infos_temporal_val.pkl`
- `nuscenes_map_anns_val.json` for validation/test map evaluation

A stock `nuscenes_infos_train.pkl` is not an interchangeable replacement. VAD's converter adds temporal history/future and ego/CAN-bus fields used by `VADCustomNuScenesDataset`; the configured `queue_length` is typically 3 for tiny configs and 4 for base configs.

## Converter contract

The repository's VAD converter is invoked through the following public argument shape:

```bash
python <converter-entry> nuscenes \
  --root-path DATA_ROOT \
  --out-dir DATA_ROOT \
  --extra-tag vad_nuscenes \
  --version v1.0 \
  --canbus CANBUS_PARENT
```

Use real paths in place of the placeholders. The converter constructs a `NuScenes` object, reads CAN-bus pose messages, filters available scenes, and writes:

- `vad_nuscenes_infos_temporal_train.pkl`
- `vad_nuscenes_infos_temporal_val.pkl`

For a test split it writes the temporal test variant instead. The converter can also export 2D annotations through the surrounding data-preparation entry point. The exact entry-point import is framework-version-sensitive, so validate the layout first and preserve the repository's argument names.

## Preflight and postflight

Before conversion:

1. Confirm the version directory contains metadata and the sensor folders are populated.
2. Confirm `CANBUS_PARENT/can_bus` exists and is readable.
3. Confirm the output directory is writable and has free space.
4. Confirm the intended `--version` matches the installed split (`v1.0-trainval`, `v1.0-test`, or the documented mini variant when supported by the converter).
5. Run `scripts/check_data_layout.py` with `--require-train --require-val` only if the PKLs already exist; omit those flags for a pre-conversion check.

After conversion:

1. Check both temporal PKLs exist and are non-empty.
2. Check the validation map annotation exists if using the VAD validation/test config.
3. Keep `data_root`, annotation filenames, map annotation path, and `queue_length` consistent across train/val/test config sections.
4. Do not start training until the plugin/config import gate also passes; see [architecture-configuration](../../architecture-configuration/SKILL.md).

## Evidence notes

The source converter's `create_nuscenes_infos` accepts `root_path`, `out_path`, `can_bus_root_path`, `info_prefix`, `version`, and `max_sweeps`; the public wrapper adds the `nuscenes` subcommand and CLI flags. The VAD dataset reads temporal agent/ego fields and vectorized map annotations, so a syntactically valid but stock PKL can still fail later.
