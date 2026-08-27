# OpenLane-V2 Devkit, Data, Submission, and Metrics

## Purpose

Read this for OpenLane-V2 scene-structure tasks: 3D lane centerlines, traffic elements, lane-lane topology, lane-traffic topology, validation, and metric interpretation. The facts here are distilled from the OpenLane-V2 docs and source evidence; future agents should use the bundled scripts rather than reopening source files.

## Task components

OpenLane-V2 evaluates scene structure from multi-view autonomous-driving images:

- `lane_centerline`: directed 3D lane centerlines. Predictions are polylines with confidence scores.
- `traffic_element`: traffic lights and road signs in the front camera view. Predictions include a bounding box, attribute, and confidence.
- `topology_lclc`: directed adjacency among lane centerlines.
- `topology_lcte`: relationship confidence between lane centerlines and traffic elements.

Traffic element attributes use the inspected devkit mapping:

| Attribute id | Meaning |
| --- | --- |
| 0 | unknown |
| 1 | red |
| 2 | green |
| 3 | yellow |
| 4 | go_straight |
| 5 | turn_left |
| 6 | turn_right |
| 7 | no_left_turn |
| 8 | no_right_turn |
| 9 | u_turn |
| 10 | no_u_turn |
| 11 | slight_left |
| 12 | slight_right |

## Data hierarchy

OpenLane-V2 data is organized around splits, segments, timestamps, camera images, and frame metadata:

```text
OpenLane-V2/
  train/<segment_id>/image/<camera>/<timestamp>.jpg
  train/<segment_id>/info/<timestamp>.json
  val/<segment_id>/image/<camera>/<timestamp>.jpg
  val/<segment_id>/info/<timestamp>.json
  test/<segment_id>/image/<camera>/<timestamp>.jpg
  test/<segment_id>/info/<timestamp>.json
  data_dict_subset_A.json
  data_dict_subset_B.json
  openlanev2.md5
  preprocess.py
```

Important layout rules:

- `image/` holds camera images; `info/` holds JSON metadata and annotations for each frame.
- `data_dict_*` files map split -> segment id -> timestamp JSON names and drive preprocessing into collection pickle files.
- The original preprocessing source collects JSON metadata into `<collection>.pkl` under the data root. Train split keeps every lane point; non-train splits subsample lane points with interval 20.
- The OpenLane-V2 challenge primary subset is `subset_A`; the repository notes that external data, including another subset, is not allowed for challenge use.

## Devkit API facts

Installed/source inspection verified these public shapes:

- `openlanev2.dataset.Collection(data_root: str, meta_root: str, collection: str)` loads `<meta_root>/<collection>.pkl` and exposes frame keys.
- `Collection.get_frame_via_identifier(identifier: tuple) -> Frame`, where the identifier is `(split, segment_id, timestamp)`.
- `Collection.get_frame_via_index(index: int) -> (tuple, Frame)`.
- `openlanev2.dataset.Frame(root_path: str, meta: dict)` exposes:
  - `get_camera_list()`
  - `get_pose()`
  - `get_image_path(camera)`
  - `get_rgb_image(camera)`
  - `get_intrinsic(camera)`
  - `get_extrinsic(camera)`
  - `get_annotations()`
  - `get_annotations_lane_centerlines()`
  - `get_annotations_traffic_elements()`
  - `get_annotations_topology_lclc()`
  - `get_annotations_topology_lcte()`
- `openlanev2.io.io` wraps `os.listdir`, OpenCV image read, JSON load, pickle dump, and pickle load.
- `openlanev2.preprocessing.check.check_results(results: dict) -> None` imported directly and validated tiny valid/invalid fixtures during environment inspection.
- `openlanev2.evaluation.evaluate(ground_truth, predictions, verbose=True)` exists in source, but a direct import failed in the inspected checkout because the evaluation file imports `check_results` from an empty preprocessing package initializer. See troubleshooting for the workaround.

## Prediction/submission schema

The challenge submission format is a top-level dict with metadata plus per-frame predictions:

```text
{
  "method": str,
  "authors": [str, ...],
  "e-mail": str,
  "institution / company": str,
  "country / region": str,       # preferably ISO 3166-recognized
  "results": {
    "<frame identifier>": {
      "predictions": {
        "lane_centerline": [
          {"id": int|string, "points": [[x, y, z], ...], "confidence": float}
        ],
        "traffic_element": [
          {"id": int|string, "attribute": int, "points": [[x1, y1], [x2, y2]], "confidence": float}
        ],
        "topology_lclc": [[float, ...], ...],
        "topology_lcte": [[float, ...], ...]
      }
    }
  }
}
```

Shape rules:

- Lane points: two-dimensional numeric matrix `#points x 3`.
- Traffic element points: numeric matrix `2 x 2`, top-left and bottom-right corners.
- IDs: unique within a frame across both `lane_centerline` and `traffic_element` predictions.
- `topology_lclc`: numeric matrix `#lane_centerline x #lane_centerline`.
- `topology_lcte`: numeric matrix `#lane_centerline x #traffic_element`.
- Matrix rows/columns must follow the order of the corresponding lane and traffic lists. A correct matrix shape with reordered objects can still produce wrong metrics.
- Ground-truth topology entries are boolean 0/1; prediction topology entries are confidence values, typically in `[0, 1]`.

## Standalone JSON validation

Use the bundled validator before any conversion to pickle or upload:

```bash
python <SKILL_DIR>/scripts/validate_openlanev2_submission.py <submission.json>
```

For CI-style output:

```bash
python <SKILL_DIR>/scripts/validate_openlanev2_submission.py <submission.json> --json-report
```

The validator is intentionally standalone and JSON-oriented. It does not import OpenLane-V2, does not require NumPy arrays, and catches common schema mistakes earlier than a full model/evaluation environment.

## Metrics summary

OpenLane-V2 Score is the average of four components:

```text
OLS = 1/4 * (DET_l + DET_t + sqrt(TOP_ll) + sqrt(TOP_lt))
```

Metric meanings:

- `DET_l`: average precision on directed 3D lane centerlines. Source metrics use Frechet-based matching over thresholds `1.0`, `2.0`, and `3.0`.
- `DET_t`: average precision on traffic elements. Source metrics use IoU distance with threshold `0.75` and average over traffic-element attributes.
- `TOP_ll`: topology quality among lane centerlines, evaluated as directed graph link prediction after matching predicted lanes to ground truth.
- `TOP_lt`: topology quality between lane centerlines and traffic elements, evaluated as bipartite graph link prediction after matching predicted vertices.
- `F-Score for 3D Lane`: separate 3D lane F-score implementation based on matching resampled lane lines.

## OpenLane-V2 mmdet3d plugin behavior

The OpenLane-V2 InternImage config uses:

- `custom_imports = dict(imports=['plugin.mmdet3d.baseline'])` so plugin importability matters before building models.
- `OpenLaneV2SubsetADataset` with `data_root` and `meta_root` set to `data/OpenLane-V2` by default.
- Collections named `data_dict_subset_A_train` and `data_dict_subset_A_val` for train/validation in the InternImage config.
- Seven cameras, with the dataset asserting that the first camera is `ring_front_center`.
- InternImage-S as `img_backbone`, DCNv3 as `core_op`, and heads for traffic elements, lane centerlines, lane-lane relationships, and lane-traffic relationships.
- Evaluation options `dump=True dump_dir=<dir>` to write `result.pkl` after `check_results`, and `visualization=True visualization_dir=<dir>` to write rendered outputs.

For command construction, use [../scripts/build_autonomous_command.py](../scripts/build_autonomous_command.py). For schema validation, use [../scripts/validate_openlanev2_submission.py](../scripts/validate_openlanev2_submission.py).
