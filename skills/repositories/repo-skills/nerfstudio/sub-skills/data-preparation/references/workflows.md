# Data preparation workflows

## Images or video with COLMAP

Use this path for ordinary camera or phone images/videos that need pose reconstruction.

```bash
ns-process-data images --data RAW_IMAGE_DIR --output-dir PROCESSED_DATA_DIR
ns-process-data video --data RAW_VIDEO_FILE --output-dir PROCESSED_DATA_DIR
```

Prerequisites: FFmpeg for video/media handling and COLMAP for reconstruction. Use the validator after conversion.

If a compatible COLMAP sparse model already exists, use the CLI's skip-COLMAP options and point to the sparse model rather than rerunning reconstruction. Do not use skip-COLMAP just to bypass a missing COLMAP install.

## Device/export captures

- Polycam: export raw data from developer mode, then run `ns-process-data polycam --data CAPTURE.zip --output-dir PROCESSED_DATA_DIR`.
- Record3D: pass the Record3D directory and optional PLY point export when available.
- Metashape and RealityCapture: export camera XML/CSV/pose files and point cloud assets as expected by the corresponding process-data mode.
- ODM: use the ODM output folder when it already contains the expected reconstruction products.
- Aria: requires Project Aria tooling; treat it as optional and verify dependencies before promising a runnable command.

## Existing Nerfstudio-format data

When a directory already contains `transforms*.json` and images, do not rerun `ns-process-data`. Validate it, then train with:

```bash
ns-train nerfacto --data PROCESSED_DATA_DIR
```

Use `nerfstudio-data --eval-mode filename` when explicit train/val/test filename lists are present and filename-based splits are desired.

## Dataparser selection

Common dataparser names include:

- `nerfstudio-data`: default processed `transforms*.json` format.
- `blender-data`: classic synthetic Blender/NeRF dataset format.
- `minimal-parser`: tiny data IO/testing layouts.
- `colmap`: use COLMAP outputs directly when compatible.
- Dataset-specific parsers such as `dnerf-data`, `phototourism-data`, `sdfstudio-data`, `nuscenes-data`, and `sitcoms3d-data`.

Dataparser options are placed after the dataparser subcommand:

```bash
ns-train nerfacto nerfstudio-data --eval-mode filename --data PROCESSED_DATA_DIR
```

When using the global `--data` alias, keep it with the method-level options:

```bash
ns-train nerfacto --data PROCESSED_DATA_DIR
```
