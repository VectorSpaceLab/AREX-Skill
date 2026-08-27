# Supervision troubleshooting

Use this root troubleshooting reference for install/import, optional dependency,
backend, deprecation, and routing problems that cut across several sub-skills.
For workflow-specific failures, use the nearest sub-skill troubleshooting file.

## Import fails or package version is unexpected

**Checks**

```bash
python -c "import supervision as sv; print(sv.__version__)"
python -m pip show supervision
```

**Fix**

- Use Python >=3.10.
- Install the base package with `pip install supervision`.
- If working inside a source checkout, install it intentionally with an editable
  install only for development. Ordinary package-usage tasks should not depend
  on a checkout being present.
- If a task needs this generated skill to match a different checkout or package
  version, read [repo provenance](repo-provenance.md) and refresh the repo skill
  when the commit, dirty state, or public API surface changed.

## OpenCV warning or backend mismatch

**Symptoms**

- Import warning says OpenCV is not installed and the fallback backend is active.
- Pixel-level drawing or video behavior differs from an OpenCV baseline.
- Webcam or GUI code fails.

**Fix**

Supervision does not require OpenCV. The fallback backend is acceptable for
package-owned image, drawing, and file-video helpers. Install exactly one native
OpenCV wheel only when the application needs it:

```bash
pip install opencv-python-headless supervision  # servers/containers
pip install opencv-python supervision           # desktop GUI/window use
```

After changing OpenCV wheels, start a fresh Python process and run:

```bash
python -c "from supervision import _cv2; print(_cv2.BACKEND_NAME)"
```

For media-specific details, use
[media-utils backend compatibility](../sub-skills/media-utils/references/backend-compatibility.md).

## Metrics extra missing

**Symptoms**

- `.to_pandas()` fails.
- A metric import complains about pandas or the metrics extra.

**Fix**

```bash
pip install "supervision[metrics]"
```

Then use [metrics](../sub-skills/metrics/SKILL.md). Numeric metric fields may
work without pandas only when the required metric modules are already importable,
but the supported route is to install the extra for evaluation workflows.

## GeoTIFF/rasterio lane missing

**Symptoms**

- `InferenceSlicer` over a rasterio-style dataset fails because `rasterio` is
  absent.
- A GeoTIFF task asks about projected rasters or windowed reads.

**Fix**

```bash
pip install "supervision[geotiff]"
```

Then use [detection-and-zones](../sub-skills/detection-and-zones/SKILL.md) for
`InferenceSlicer` behavior and
[media-utils](../sub-skills/media-utils/SKILL.md) for raster/image backend
issues. Plain NumPy image slicing does not need this extra.

## Optional model framework dependency missing

**Symptoms**

- `ultralytics`, `transformers`, `mediapipe`, `detectron2`, `mmdet`,
  `inference`, or another model package is not installed.
- A model-download example cannot fetch weights or needs credentials.

**Fix**

Supervision adapters convert already-produced results. They do not install
model frameworks, download weights, or supply API keys. Install only the model
package that the user selected, keep heavy imports inside model-specific code,
and route adapter normalization to
[detection-and-zones](../sub-skills/detection-and-zones/SKILL.md) or
[tracking-keypoints](../sub-skills/tracking-keypoints/SKILL.md).

## Deprecated APIs appear in user code

| Deprecated/compatibility surface | Preferred path |
| --- | --- |
| `supervision.keypoint` | `supervision.key_points` or top-level `sv.KeyPoints` and keypoint annotators |
| `KeyPoints.confidence` / `confidence=` | `keypoint_confidence` |
| `sv.ByteTrack` | External `trackers.ByteTrackTracker` when available; compatibility fallback only when needed |
| old ByteTrack args `track_thresh`, `track_buffer`, `match_thresh` | `track_activation_threshold`, `lost_track_buffer`, `minimum_matching_threshold` |
| `sv.LMM` and `Detections.from_lmm` | `sv.VLM` and `Detections.from_vlm` |
| `create_tiles`, public validation shims, old dataset/mask import paths | Current public helpers described in the relevant sub-skill |

Use [tracking-keypoints](../sub-skills/tracking-keypoints/SKILL.md) for tracker
and keypoint migration, and
[detection-and-zones](../sub-skills/detection-and-zones/SKILL.md) for VLM
adapter migration.

## Data alignment problems

**Symptoms**

- A sliced `Detections` or `KeyPoints` object has mismatched labels, confidence,
  masks, or metadata.
- CSV/JSON export rows do not line up with boxes.
- Metrics report wrong classes despite correct geometry.

**Fix**

- Filter container objects (`detections[mask]`, `key_points[mask]`) rather than
  slicing individual arrays independently.
- Store per-row metadata in `data` arrays/lists aligned with row count.
- Import constants such as `CLASS_NAME_DATA_FIELD` and
  `ORIENTED_BOX_COORDINATES` from `supervision.config`.
- Route container alignment issues to [detection-and-zones](../sub-skills/detection-and-zones/SKILL.md)
  or [tracking-keypoints](../sub-skills/tracking-keypoints/SKILL.md).

## Wrong route for the task

- Visualization with `scene` + `Detections`: [annotators](../sub-skills/annotators/SKILL.md).
- Primitive drawing, image/video I/O, file utilities, and backend diagnostics:
  [media-utils](../sub-skills/media-utils/SKILL.md).
- Dataset layout and format conversion: [datasets](../sub-skills/datasets/SKILL.md).
- Metric result interpretation: [metrics](../sub-skills/metrics/SKILL.md).
- Tracking identity/keypoints: [tracking-keypoints](../sub-skills/tracking-keypoints/SKILL.md).
- Detections/model adapters/zones/slicers/sinks: [detection-and-zones](../sub-skills/detection-and-zones/SKILL.md).
