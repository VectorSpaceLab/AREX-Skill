# Evaluation and result conversion

## KITTI annotation contract

`kitti_common.get_label_anno` returns one dict per frame with parallel arrays:

- `name [N]`, `truncated [N]`, `occluded [N]`, `alpha [N]`, `bbox [N,4]`
- `dimensions [N,3]` in camera `[l,h,w]` order (the text parser converts disk
  `h,w,l` to this order)
- `location [N,3]`, `rotation_y [N]`, and `score [N]`

`empty_result_anno()` supplies correctly shaped zero-length arrays. Build a
result with `get_start_result_anno()` then stack every field, or use the empty
schema when there are no detections. `annos_to_kitti_label` serializes each row;
`kitti_result_line` defaults missing nonessential fields but requires `name` and
rejects unknown keys. Ground truth and detections must have the same frame order,
parallel lengths, valid class strings, and finite geometry.

`get_official_eval_result(gt_annos, dt_annos, current_classes,
difficultys=[0,1,2], z_axis=1, z_center=1.0)` returns `{result, detail}`. The
result text reports `bbox AP`, `bev AP`, and `3d AP` per class/overlap; detail
contains per-difficulty arrays. `get_coco_eval_result` evaluates ten overlap
levels between configured bounds and returns similarly named metrics.

`eval_class_v3(..., metric, min_overlaps, ...)` returns arrays with shape
`[num_class,num_difficulty,num_minoverlap,41]` for `precision`, `recall`,
`orientation`, and `thresholds`. `metric=0/1/2` means image bbox/BEV/3-D.
`get_mAP(precision)` samples every fourth value of the 41-point curve, divides
by 11, and multiplies by 100; reported AP is therefore percentage points.
`z_axis` and `z_center` must match the box representation: historical KITTI
camera defaults are `z_axis=1,z_center=1.0`, while the NuScenes unofficial KITTI
path uses lidar `z_axis=2,z_center=0.5` and warns that image bbox AP is invalid.

### Minimal perfect-match fixture

For a CPU-safe evaluator fixture, make one frame and one `Car` in both arrays:

```python
common = {
    "name": np.array(["Car"]),
    "bbox": np.array([[0., 0., 50., 50.]]),
    "dimensions": np.array([[4., 1.6, 1.5]]),  # camera l,h,w schema
    "location": np.array([[10., 0.5, 20.]]),
    "rotation_y": np.array([0.0]),
    "alpha": np.array([-10.0]),
    "truncated": np.array([0.0]),
    "occluded": np.array([0]),
    "score": np.array([1.0]),
}
gt = [common.copy()]
dt = [{k: v.copy() for k, v in common.items()}]
```

Use `z_axis`/`z_center` matching the chosen frame and call the evaluator only if
its dependencies are available. A perfect match should produce a true positive
and high AP for the selected class; if it does not, diagnose class spelling,
array lengths, bbox/dimension order, difficulty filtering, and frame alignment
before changing thresholds. This fixture validates annotation plumbing, not
model quality.

## NuScenes submission schema

The dataset conversion writes `results_nusc.json` with:

```json
{
  "meta": {"use_camera": false, "use_lidar": false, "use_radar": false,
           "use_map": false, "use_external": false},
  "results": {
    "<sample_token>": [
      {"sample_token":"<token>", "translation":[x,y,z],
       "size":[w,l,h], "rotation":[qw,qx,qy,qz], "velocity":[vx,vy],
       "detection_name":"car", "detection_score":0.9,
       "attribute_name":"vehicle.parked"}
    ]
  }
}
```

The exact quaternion element order is the `pyquaternion.Quaternion.elements`
list produced by the source path; do not hand-write a different convention.
Class names follow the dataset mapping (`car`, `truck`, `bus`, `pedestrian`,
`bicycle`, `motorcycle`, `traffic_cone`, `barrier`, `construction_vehicle`,
`trailer`). Default attributes are class-dependent; static classes may use an
empty attribute. `v1.0-mini` maps to `mini_train`, and `v1.0-trainval` maps to
`val` in the wrapper. The external devkit evaluator is invoked with
`config_factory(eval_version)` and writes `metrics_summary.json`.

The wrapper summarizes per-class `label_aps` at center-distance thresholds
`0.5, 1.0, 2.0, 4.0` (the exact keys come from the selected devkit config) and
per-class `label_tp_errors`. AP is printed as a percentage; TP errors remain
numeric errors, so lower is generally better. A high distant AP with poor
near-distance AP may indicate localization error or sparse data, not a good
box match.

The historical Fire entry point is equivalent to the following placeholder
command; it requires a real NuScenes root, a result JSON, and a writable output
folder, and may write `metrics_summary.json` plus curve artifacts:

```bash
python -m second.data.nusc_eval \\
  --root_path=<NUSCENES_ROOT> --version=v1.0-mini \\
  --eval_version=cvpr_2019 --res_path=<RESULTS_JSON> \\
  --eval_set=mini_train --output_dir=<OUTPUT_DIR>
```

Run it only after checking the JSON schema above and confirming the devkit
version/config. A missing `metrics_summary.json`, unknown token, invalid class,
or version/eval-set mismatch is a data/config failure, not evidence of poor AP.

## Interpretation and safe checks

1. Confirm the evaluator's class set and frame count before reading a mean.
2. Read AP by class and threshold, not only a global average. A class with no
   valid ground truth can make a score meaningless; report that explicitly.
3. Separate bbox, BEV, and 3-D AP. A strong bbox score with weak 3-D AP usually
   points to depth, height origin, dimension order, or yaw/calibration errors.
4. Compare score threshold, NMS, and maximum detections only after the perfect
   match fixture and annotation schema pass.
5. Treat historical README numbers as intent evidence, not reproduction proof.
   This generated route does not claim detector or evaluator execution was
   verified in the current modern dependency environment.
