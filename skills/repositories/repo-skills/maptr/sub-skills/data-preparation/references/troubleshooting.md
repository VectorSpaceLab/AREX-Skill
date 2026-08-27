# Data-preparation troubleshooting

Use the bundled checker first. Treat any `ERROR` as a stop condition for
conversion. A warning is actionable before training but does not necessarily
block a filesystem-only handoff.

| Symptom | Likely cause | Recovery | Stop condition |
|---|---|---|---|
| nuScenes `maps/` is missing or empty | Raw release is incomplete or the root points at its parent/child | Set `--root` to the directory containing `maps`, `samples`, and `sweeps`; restore the map expansion | Do not vectorize without the map expansion |
| CAN bus reported missing | `can_bus` was nested under `nuscenes/`, or `--canbus` points at the wrong level | Pass the parent containing `can_bus` to `--canbus`; move only with an explicit data-owner decision | Do not claim temporal CAN data is ready when the expansion is absent |
| temporal pkl missing | Converter was not run, wrote to another `--out-dir`, or a standard non-temporal pkl was used | Inspect the converter output directory; run the documented nuScenes converter after imports and raw checks pass | Do not substitute `nuscenes_infos_train.pkl` for `nuscenes_infos_temporal_train.pkl` |
| pkl split mismatch | A train config points at val/test or a mini/release output has another prefix | Align `ann_file` basename and config split; use the exact generated filename | Stop if the file exists but its release/split is unknown |
| AV2 `train`, `val`, or `test` missing | Only one split was downloaded, or `--root` points at a split rather than `sensor/` | Acquire/attach the missing split or explicitly scope a nonstandard converter; pass the sensor parent | The bundled converter loops all three splits, so a missing split blocks the reference command |
| AV2 log has no `map/` | Incomplete log or wrong AV2 directory level | Restore the log's map directory; ensure the checker sees the log under the correct split | Do not run map conversion without a map archive |
| AV2 map archive count is 0 | Archive was not downloaded or has a nonstandard name | Place the supplied archive at `map/log_map_archive_<name>.json`, or document an adapter | Stop |
| AV2 map archive count is greater than 1 | Duplicate archives or stale generated copy | Retain the one authoritative archive after data-owner confirmation | Stop; converter raises on duplicates |
| AV2 archive is malformed JSON | Partial transfer, compression was not unpacked, or wrong file | Re-copy/unpack the archive and validate with a JSON parser | Stop; do not delete an original without approval |
| AV2 conversion reports discarded samples | Closest image/lidar lookup returned `None` for a timestamp | Inspect sensor synchronization and camera names; retain the converter's discarded count | Stop if all samples in a split are discarded |
| `ModuleNotFoundError: av2` | AV2 API is not installed in the selected environment | Install and prove the documented AV2 dependency in an isolated environment | Do not bypass the loader with guessed paths |
| mmcv/numpy/torch ABI or import error | Legacy binary wheel does not match the Python, torch, or CUDA runtime | Stop; use a clean compatible environment and re-run import probes | Never infer compatibility from one successful pure-Python import |
| Geometric Kernel Attention build fails | Legacy CUDA/toolchain mismatch or extension was not built | Route to model-configuration; record the exact toolchain failure and defer model execution | This data route cannot repair the extension |
| map location is unknown | Pkl metadata does not use one of the four supported nuScenes locations | Inspect release and scene metadata; do not rename locations without evidence | Stop vectorization for that sample |
| `id2map[log_id]` lookup fails | AV2 pkl and raw logs came from different conversions | Keep pkl and raw root from the same conversion; regenerate after alignment | Stop |
| vector class error | Config requested a class other than `divider`, `ped_crossing`, or `boundary` | Correct `map_classes` or route the new geometry to a code change/design review | Do not silently map to `others` |
| empty vectors for a valid sample | Patch contains no geometry, invalid/intersected geometry was filtered, or map pose is wrong | Check pose, patch range, map class, and geometry validity with a small read-only inspection | Do not fabricate a vector to satisfy a tensor shape |
| fixed-point shape differs from `[N,20,2]` | Fixed count is unset/negative, config differs, or a shifted property was inspected | Check `fixed_ptsnum_per_line`; distinguish base `[N,20,2]` from shifted `[N,S,20,2]` | Stop if labels and vectors are not aligned |
| malformed coordinate arrays | 3D or ragged points were supplied where 2D geometry is expected | Preserve AV2 3D source only until the vectorizer's city-to-ego projection; validate final x/y arrays | Stop on nonnumeric, fewer-than-two-point lines |
| checker says path is outside root | A relative path was resolved from the wrong current directory or a symlinked data root is ambiguous | Use absolute `--root`, `--canbus-root`, and annotation paths; verify real ownership | Stop if a path escapes the declared data root |

## Difficult layout cases

### CAN bus at the wrong level and missing temporal pkl

Create a nuScenes fixture with `maps/`, `samples/`, `sweeps/`, and
`v1.0-trainval/` under the root, but put `can_bus/` under the nuScenes root
instead of the parent. Omit `nuscenes_infos_temporal_train.pkl`. Run:

```bash
python <skill-root>/scripts/check_dataset_layout.py \
  --dataset nuscenes --root "$FIXTURE/nuscenes" \
  --canbus-root "$FIXTURE" --check-annotations
```

Expected assertions: a CAN-bus placement error names the expected
`$FIXTURE/can_bus` path and an annotation error names
`nuscenes_infos_temporal_train.pkl`. The checker must return 1 and must not
move the directory or create a pkl.

Recovery: correct the CAN-bus root/layout, then run the full converter only
with approved downloaded data. A temporal pkl can only be accepted after a
real converter output is identified; an empty placeholder is not a recovery.

### AV2 missing split and malformed map archive

Create `sensor/train/log-a/map/log_map_archive_a.json` with `{}` and
`sensor/val/log-b/map/log_map_archive_b.json` with invalid JSON. Omit
`sensor/test/`. Run:

```bash
python <skill-root>/scripts/check_dataset_layout.py \
  --dataset av2 --root "$FIXTURE/sensor" --check-annotations
```

Expected assertions: the result names missing `test`, malformed `log-b` JSON,
and missing `av2_map_infos_train.pkl`/`val.pkl` (and test if annotation checks
are enabled). It must not treat `{}` as a valid semantic map and must return 1.

Recovery: restore all split trees and authoritative AV2 archives, then let the
AV2 API validate semantic schema during a bounded conversion. The checker can
only validate JSON syntax and archive cardinality, not lane-segment fields.

## What this checker cannot prove

It cannot prove image readability, lidar binary shape, camera calibration,
scene continuity, temporal link correctness, AV2 semantic map fields, pkl
contents, class/label alignment, or custom extension compatibility. Record
these as unresolved rather than converting warnings into success.