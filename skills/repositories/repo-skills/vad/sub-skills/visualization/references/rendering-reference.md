# VAD rendering reference

## Inputs

The documented VAD rendering entry point accepts:

```bash
python <visualization-entry> --result-path RESULTS.pkl --save-path OUTPUT_DIR
```

The repository documentation describes the result as a `prefix_results_nusc.pkl`-style artifact saved during evaluation. The checked visualization implementation expects a top-level mapping containing at least:

- `results`: mapping from sample token to detection records.
- `map_results`: mapping from sample token to vector-map predictions, including `vectors`.
- `plan_results`: mapping from sample token to planning trajectory/mode information.

A detection record is converted into a custom box with fields evidenced by the renderer and dataset formatter, including `sample_token`, `translation`, `size`, `rotation`, `velocity`, `fut_traj`, `detection_name`, `detection_score`, `attribute_name`, and optional `ego_translation`/point counts. Future trajectories are six-step in the supplied configs/rendering code.

Use [scripts/inspect_result_artifact.py](../scripts/inspect_result_artifact.py) first. Pickle is executable/trusted-input territory: inspect only artifacts you trust.

## Data and coordinate preflight

Rendering uses nuScenes records for each sample token, camera calibration, ego pose, sensor paths, and LiDAR data. The renderer enumerates the six camera channels:

`CAM_FRONT`, `CAM_FRONT_RIGHT`, `CAM_BACK_RIGHT`, `CAM_BACK`, `CAM_BACK_LEFT`, `CAM_FRONT_LEFT`.

It transforms boxes between global, ego, sensor, and camera frames and draws vector maps, predicted agent future trajectories, and ego planning trajectories. A valid result without matching nuScenes sample tokens cannot render correctly.

Before rendering:

1. Confirm `RESULTS.pkl` has the top-level mappings and sample tokens.
2. Confirm the data root contains the corresponding nuScenes version metadata, samples/sweeps, maps, and calibration/pose tables.
3. Confirm the six camera files and `LIDAR_TOP` exist for representative tokens.
4. Use an output directory with enough space; video/image creation can be large.
5. Ensure the checkpoint/evaluation used the correct image normalization. Released weights require the legacy normalization described in the training route.

## Interpretation

- Green/ground-truth and blue/predicted overlays are used by the source renderer; verify the legend in the produced output rather than assuming colors in a modified renderer.
- A missing `map_results` or `plan_results` section can prevent the VAD-specific overlay even when object boxes exist.
- Empty boxes may be a score threshold or sample-token mismatch, not necessarily a model failure.
- Geometrically shifted boxes/trajectories usually indicate calibration/pose, frame, version, or normalization mismatch.

Construction intentionally skipped full rendering because no external dataset/result artifact was available.
