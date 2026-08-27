# Multi-Animal Tracking Workflows

## 1. Fast path for most projects

If the model is already trained and you want the default modern behavior, let `analyze_videos` do the whole job:

```python
deeplabcut.analyze_videos(
    config_path,
    videos,
    auto_track=True,
    n_tracks=None,
    animal_names=None,
    identity_only=False,
)
```

Use this when you want a final `.h5` without manually tuning tracklets.
If the project uses a conditional top-down model, tracking happens during analysis and the CTD branch should be used instead of manual convert/stitch calls.

## 2. Manual tracklet-tuning path

Use this when the auto-tracked output needs inspection or parameter tuning:

```python
deeplabcut.analyze_videos(
    config_path,
    videos,
    auto_track=False,
)
deeplabcut.convert_detections2tracklets(
    config_path,
    videos,
    track_method="ellipse",
    identity_only=False,
)
deeplabcut.stitch_tracklets(
    config_path,
    videos,
    track_method="ellipse",
    n_tracks=None,
    animal_names=None,
)
```

Practical tuning order:
1. inspect the analyzed detections and assemblies,
2. tune the tracker family (`ellipse`, `box`, or `skeleton`),
3. adjust `boundingboxslack`, `iou_threshold`, `max_age`, or `min_hits` in the inference config,
4. rerun conversion,
5. restitch the tracklets.

If the project has one multianimal bodypart, the box tracker is expected.

## 3. Identity-aware variant

If the project was trained with `identity: true`, keep the individual names stable across labeling and output naming. Then try:

```python
deeplabcut.convert_detections2tracklets(
    config_path,
    videos,
    track_method="ellipse",
    identity_only=True,
)
```

Use `identity_only=True` only when the identity head was learned. If identity labels are inconsistent, fix the config and labels first rather than forcing the tracker.

## 4. ReID-assisted variant

Use transformer reID when baseline tracking still swaps animals at crossings or with long occlusions:

```python
deeplabcut.transformer_reID(
    config_path,
    videos,
    track_method="ellipse",
    n_tracks=3,
    n_triplets=1000,
    train_epochs=100,
)
```

This wrapper mines triplets from baseline tracklets, trains the transformer, and then stitches with the generated checkpoint.
If you already have a trained checkpoint and only want to restitch baseline tracklets, call `stitch_tracklets(..., transformer_checkpoint=<checkpoint>)` directly.

## 5. CTD direct-tracking branch

For conditional top-down models, do not build manual tracklets. Instead, analysis handles tracking directly:

```python
deeplabcut.analyze_videos(
    config_path,
    videos,
    ctd_tracking=True,
    ctd_conditions=CTD_CONDITIONS,
)
```

CTD workflows are an analysis-time branch, not a convert/stitch branch.

## 6. Output validation order

Validate in this order:
1. raw detection files exist,
2. tracklet file exists and its suffix matches the chosen tracker,
3. final `.h5` exists and has the expected number of animals,
4. if reID was used, the checkpoint and feature dictionary exist,
5. if the outputs look wrong, hand off labeled-video rendering to the postprocessing sub-skill.

## 7. When to stop and reroute

- project or config creation problems -> setup sub-skill
- missing labels or training data -> dataset sub-skill
- training or pose-analysis failures -> PyTorch training/evaluation sub-skill
- filtering or labeled-video requests -> postprocessing sub-skill
