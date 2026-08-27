---
name: "data-conversion"
description: "Routes KITTI and nuScenes data-layout, detection-conversion, and
  schema-validation work for AB3DMOT inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# data-conversion

Use this sub-skill when you need to prepare AB3DMOT-ready KITTI or nuScenes inputs, convert nuScenes detector output into KITTI-style intermediate files, or validate detection rows before they reach tracking.

This route is about input readiness, not tracking execution. It helps you confirm that the trees, sequence names, detection rows, and dataset category IDs line up before a future tracker run.

## Use this route for

- Checking KITTI and nuScenes data roots before any tracker run.
- Converting raw nuScenes detection JSON into KITTI object-format files and then into AB3DMOT input files.
- Verifying the 15-column, comma-separated detection schema.
- Confirming category folders such as `det_name_Car_val` and `det_name_all_val`.
- Reconciling sequence names, correspondence files, and category IDs.
- Catching category-folder mismatches before they turn into silent tracking errors.
- Explaining why a downstream tracker cannot find a sequence, class, or split.

## Do not use this route for

- Running `main.py` tracking. Use `tracking-pipeline`.
- Scoring, thresholding, or visualizing outputs. Use `evaluation-visualization`.
- Repository-wide refactors or model changes.
- Rewriting the full nuScenes converter into the skill tree.

## Read first

- [`references/data-formats.md`](references/data-formats.md) for the row schema, category maps, and folder naming rules.
- [`references/kitti-data-layout.md`](references/kitti-data-layout.md) for KITTI roots, split mapping, and expected trees.
- [`references/nuscenes-conversion.md`](references/nuscenes-conversion.md) for raw nuScenes data, conversion routes, and method names.
- [`references/troubleshooting.md`](references/troubleshooting.md) for the most common layout, naming, dependency, and schema failures.

## Skill-owned script

- [`scripts/validate_ab3dmot_detection.py`](scripts/validate_ab3dmot_detection.py) — validate one or more AB3DMOT detection text files without importing repo code.

## Expected trees

### KITTI

```text
./data/KITTI/
  tracking/
    training/
      calib/
      image_02/
      label_02/
      oxts/
      velodyne/
    testing/
      calib/
      image_02/
      oxts/
      velodyne/
  detection/
    pointrcnn_Car_val/0001.txt
    pointrcnn_Pedestrian_val/0001.txt
    pointrcnn_Cyclist_val/0001.txt
    pointrcnn_all_val/0001.txt
```

### nuScenes

```text
./data/nuScenes/
  data/
    samples/
    sweeps/
    v1.0-mini/
    v1.0-test/
    v1.0-trainval/
  nuKITTI/
    tracking/
      produced/
      val/
      test/
    object/
      produced/
  detection/
    centerpoint_Car_val/scene-0003.txt
    centerpoint_all_val/scene-0003.txt
```

## Conversion stages

1. Confirm the dataset root and split name.
2. Confirm the detector name matches the folder prefix.
3. If you are on nuScenes, build or refresh the KITTI-style `nuKITTI` tree.
4. If you are on nuScenes, convert detector JSON into KITTI object-format frames.
5. Aggregate frame files into per-sequence AB3DMOT detection files.
6. Validate a sample file before handing off the full tree.

## Validation gate

Before handing off, confirm all of these points:

- The delimiter is a comma, not a space.
- Every non-empty row has exactly 15 numeric fields.
- The second column is a valid category ID for the dataset.
- The row order preserves the intended frame order.
- Empty files only appear when a sequence truly has no detections.
- Folder names match `det_name_<Category>_<split>` exactly.

## Notes

- The tracker reads comma-separated files with 15 numeric fields per row.
- The second column is the dataset-specific category ID.
- `main.py` only consumes the categories listed in the dataset config.
- nuScenes conversion may emit extra categories, but the default config ignores those folders.
- Use a representative detection file from the user-provided/source checkout tree as a first sanity check; this generated skill does not bundle a dataset sample.
- Intermediate nuScenes correspondence files are required for aggregation.

## Cross-links

- If the layout is correct and you need to run the tracker, switch to `tracking-pipeline`.
- If the inputs are ready and you need to score or visualize results, switch to `evaluation-visualization`.
