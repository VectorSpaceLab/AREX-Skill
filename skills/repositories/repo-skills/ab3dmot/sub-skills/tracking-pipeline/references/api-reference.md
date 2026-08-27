# AB3DMOT Tracker API Reference

This reference is for direct, in-memory use or inspection of AB3DMOT's tracker API. Use [tracking-workflow.md](tracking-workflow.md) for command-level runs through `main.py`.

## Import prerequisites

Direct API use requires Python to import:

- `AB3DMOT_libs.model.AB3DMOT`
- `AB3DMOT_libs.box.Box3D`
- numeric dependencies such as NumPy, SciPy, FilterPy, Numba, and EasyDict
- the Xinshuo toolbox modules used by AB3DMOT utilities

If imports fail, run [../scripts/smoke_track_synthetic.py](../scripts/smoke_track_synthetic.py) to get a concise missing-dependency report.

## Key signatures

Installed-package inspection verified these signatures:

| Object | Signature | Use |
| --- | --- | --- |
| `AB3DMOT` | `AB3DMOT(cfg, cat, calib=None, oxts=None, img_dir=None, vis_dir=None, hw=None, log=None, ID_init=0)` | Create one tracker for one dataset/detector/category/sequence stream. |
| `AB3DMOT.track` | `track(self, dets_all, frame, seq_name)` | Advance the tracker exactly one frame and return results plus affinity. |
| `Box3D` | `Box3D(x=None, y=None, z=None, h=None, w=None, l=None, ry=None, s=None)` | 3D box object used by matching and distance metrics. |
| `data_association` | `data_association(dets, trks, metric, threshold, algm='greedy', trk_innovation_matrix=None, hypothesis=1)` | Assign detections to predicted tracklets by affinity. |

## Minimal config object for direct API use

`AB3DMOT.__init__` expects attribute access, not necessarily a full YAML-backed object. For direct smoke tests, a `types.SimpleNamespace` is enough when it contains:

```python
cfg = SimpleNamespace(
    dataset="KITTI",
    det_name="pointrcnn",
    ego_com=False,
    vis=False,
    affi_pro=True,
    num_hypo=1,
)
```

For real sequence tracking, also align the config with the dataset, detector, category, calibration, and ego-motion data used by the stream. Command-level `main.py` additionally uses `save_root`, `split`, `cat_list`, and `score_threshold`.

## Constructing `AB3DMOT`

Typical direct construction:

```python
from types import SimpleNamespace
from AB3DMOT_libs.model import AB3DMOT

cfg = SimpleNamespace(dataset="KITTI", det_name="pointrcnn", ego_com=False, vis=False, affi_pro=True, num_hypo=1)
tracker = AB3DMOT(cfg, cat="Car", calib=None, oxts=None, img_dir=None, vis_dir=None, hw={"image": (375, 1242), "lidar": (720, 1920)}, log=None, ID_init=1)
```

Guidance:

- Use one tracker instance for one category and one sequence stream. Recreating the tracker each frame resets state and breaks ID continuity.
- Use `ID_init` to continue a global ID counter across category loops if you need non-overlapping IDs.
- Set `ego_com=False` unless you provide both calibration and ego poses. Command-level runs pass those through the repository initialization path.
- Set `vis=False` unless image files, calibration, OpenCV, and output visualization directories are ready.

## `track(dets_all, frame, seq_name)` input contract

`track` must be called once for every frame in order, even when there are no detections, so that Kalman prediction, track aging, deletion, and affinity bookkeeping stay consistent.

`dets_all` is a dictionary with two arrays:

| Key | Shape | Content |
| --- | --- | --- |
| `"dets"` | `(N, 7)` float array | Raw 3D boxes in `[h, w, l, x, y, z, theta]` order. |
| `"info"` | `(N, 7)` float array | Side info in `[alpha, type_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, score]` order. |

Empty frames should use arrays with shape `(0, 7)` for both keys.

Example one-frame input:

```python
dets_all = {
    "dets": np.array([[1.56, 1.60, 3.80, 2.0, 1.5, 20.0, -1.57]], dtype=float),
    "info": np.array([[-1.57, 2.0, 700.0, 170.0, 900.0, 320.0, 0.95]], dtype=float),
}
results, affinity = tracker.track(dets_all, frame=0, seq_name="synthetic")
```

The full detection-file schema used by `main.py` is transformed into this dict by selecting frame-specific rows, taking columns `7:14` as `dets`, and combining the final alpha column with columns `1:7` as `info`.

## Return contract

For the single-hypothesis path (`num_hypo: 1`), `track` returns:

```python
results, affinity = tracker.track(...)
```

- `results` is a one-element list.
- `results[0]` is an `(M, 15)` float array.
- Each output row is:

```text
[h, w, l, x, y, z, theta, track_id, alpha, type_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, score]
```

The number of output rows can differ from the number of input detections because unmatched detections create tracks, old tracks can be predicted, tracks below `min_hits` can be withheld after startup, and stale tracks can be removed after `max_age`.

The verified synthetic KITTI Car smoke behavior was:

- one input detection on frame `0`;
- one `(1, 15)` output row;
- output track ID `1`;
- processed affinity shape `(0, 1)` because there were no previous active outputs and one current output.

## Affinity matrix interpretation

The raw association affinity is computed between current detections and predicted existing tracks. The matrix values are similarities:

- IoU/GIoU metrics use larger-is-better overlap-style values.
- Distance metrics are negated so larger is better; thresholds are internally negated for `dist_3d`, `dist_2d`, and `m_dis`.

When `cfg.affi_pro` is true, `process_affi` converts the raw matrix into past-active-output-tracklet by current-active-output-tracklet order. This is the processed matrix saved by `main.py`.

Important shape cases:

- First frame with one birth: `(0, 1)` processed affinity.
- A frame with no current active outputs can have zero columns.
- If `cfg.affi_pro` is false, the returned matrix follows the raw detection-by-predicted-tracklet shape.

## `Box3D` format conversions

`Box3D` stores camera-coordinate boxes with:

```text
x, y, z, h, w, l, ry, s
```

Important class methods:

| Method | Order |
| --- | --- |
| `Box3D.array2bbox_raw(data)` | input `[h, w, l, x, y, z, theta]` plus optional score |
| `Box3D.bbox2array_raw(bbox)` | output `[h, w, l, x, y, z, theta]` plus optional score |
| `Box3D.array2bbox(data)` | input `[x, y, z, theta, l, w, h]` plus optional score |
| `Box3D.bbox2array(bbox)` | output `[x, y, z, theta, l, w, h]` plus optional score |
| `Box3D.box2corners3d_camcoord(bbox)` | eight 3D corners in rectified camera coordinates |

Common pitfall: detection arrays entering `track` are raw `[h,w,l,x,y,z,theta]`, but Kalman state and matching arrays use internal `[x,y,z,theta,l,w,h]` order.

## Tracker parameter table

`AB3DMOT.get_param(cfg, cat)` selects matching algorithm, metric, threshold, minimum hits, and maximum age from dataset, detector, and category. These branches are the reason detector names must be validated before running tracking.

### KITTI, `pointrcnn` or `pvrcnn`

| Category | Algorithm | Metric | Threshold stored by tracker | `min_hits` | `max_age` |
| --- | --- | --- | ---: | ---: | ---: |
| `Car` | Hungarian | `giou_3d` | `-0.2` | 3 | 2 |
| `Pedestrian` | Greedy | `giou_3d` | `-0.4` | 1 | 4 |
| `Cyclist` | Hungarian | `dist_3d` | `-2` | 3 | 4 |

### nuScenes, `centerpoint`

| Category | Algorithm | Metric | Threshold stored by tracker | `min_hits` | `max_age` |
| --- | --- | --- | ---: | ---: | ---: |
| `Car` | Greedy | `giou_3d` | `-0.4` | 1 | 2 |
| `Pedestrian` | Greedy | `giou_3d` | `-0.5` | 1 | 2 |
| `Truck` | Greedy | `giou_3d` | `-0.4` | 1 | 2 |
| `Trailer` | Greedy | `giou_3d` | `-0.3` | 3 | 2 |
| `Bus` | Greedy | `giou_3d` | `-0.4` | 1 | 2 |
| `Motorcycle` | Greedy | `giou_3d` | `-0.7` | 3 | 2 |
| `Bicycle` | Greedy | `dist_3d` | `-6` | 3 | 2 |

### nuScenes, `megvii`

| Category | Algorithm | Metric | Threshold stored by tracker | `min_hits` | `max_age` |
| --- | --- | --- | ---: | ---: | ---: |
| `Car` | Greedy | `giou_3d` | `-0.5` | 1 | 2 |
| `Pedestrian` | Greedy | `dist_3d` | `-2` | 1 | 2 |
| `Truck` | Greedy | `giou_3d` | `-0.2` | 1 | 2 |
| `Trailer` | Greedy | `giou_3d` | `-0.2` | 3 | 2 |
| `Bus` | Greedy | `giou_3d` | `-0.2` | 1 | 2 |
| `Motorcycle` | Greedy | `giou_3d` | `-0.8` | 3 | 2 |
| `Bicycle` | Greedy | `giou_3d` | `-0.6` | 3 | 2 |

## Matching and distance notes

`data_association`:

1. Converts boxes to an affinity matrix using `iou`, `dist3d`, `dist_ground`, or Mahalanobis-like distance.
2. Solves matching with either Hungarian assignment (`algm='hungar'`) or the repository's greedy matcher.
3. Drops matches below threshold.
4. Returns matches, unmatched detections, unmatched trackers, total cost, and the affinity matrix.

Distance metrics are negated before matching. That means a threshold of `2` meters in source parameter tuning becomes `-2` inside the tracker.

## Kalman filter notes

Each born track uses `KF` with a linear FilterPy `KalmanFilter`:

- state dimension `10`: `[x, y, z, theta, l, w, h, dx, dy, dz]`;
- measurement dimension `7`: `[x, y, z, theta, l, w, h]`;
- constant-velocity transition for `x`, `y`, and `z`;
- high initial uncertainty for velocity;
- smaller process uncertainty for velocity components.

During updates, AB3DMOT corrects orientation so predicted and observed yaw remain within an acute-angle equivalent before the Kalman update. If ego-motion compensation is enabled and ego poses/calibration are present, predicted tracks are compensated into the current camera frame before association.

## Multi-hypothesis caution

The public configs set `num_hypo: 1`. The utility initializer contains a branch for `num_hypo > 1`, but the corresponding multi-hypothesis tracker import is not active in the inspected code. Treat `num_hypo > 1` as experimental or stale until an integrated verification run proves it works.
