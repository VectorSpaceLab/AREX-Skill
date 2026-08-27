# Dataset-preparation troubleshooting

## Missing raw folders

**Symptom:** the layout checker reports missing `samples/`, `sweeps/`, `maps/`, or `v1.0-trainval/`.

**Likely fix:** re-extract the nuScenes release so those folders sit directly under the configured data root. The camera-only BEVFormer route still needs the LiDAR folders for metadata generation.

## Missing CAN-bus tree

**Symptom:** the layout checker reports a missing CAN-bus root, or the converter later produces zeroed pose records for some scenes.

**Likely fix:** extract the CAN-bus archive and point the checker or dataset-preparation flow at the extracted folder. If the tree is empty or incomplete, re-unzip it.

## Missing temporal info files

**Symptom:** the layout checker reports that `nuscenes_infos_temporal_train.pkl` or `nuscenes_infos_temporal_val.pkl` is missing.

**Likely fix:** regenerate the temporal info files with the project dataset-preparation workflow and keep the output directory aligned with `data_root`.

**Extra case:** if `--expect-test` is enabled and `nuscenes_infos_temporal_test.pkl` is missing, make sure the raw test split is present before regenerating.

## Wrong ann-file names

**Symptom:** the dataset loader cannot find the annotation file even though the raw nuScenes tree exists.

**Likely fix:** point `ann_file` at the temporal pkl names used by BEVFormer, not at a default nuScenes info file from another workflow.

## V2 frame or mono-config issues

**Symptom:** BEVFormerV2 fails to assemble temporal samples, or the auxiliary monocular branch is empty.

**Likely fix:**

- keep `0` in the `frames` tuple
- keep the frame offsets scene-local
- provide a valid `mono_cfg` when the V2 training branch expects one

If you only need the current frame, use `frames=(0,)`.

## Layout passes but imports still fail

**Symptom:** the checker passes, but the dataset still does not build.

**Likely fix:** this is usually an installation or registry problem rather than a data-layout problem. Hand off to installation-and-configs.

## Checker scope

The bundled checker validates path presence only. It does not inspect dataset contents, train/eval metrics, or model configuration settings.
