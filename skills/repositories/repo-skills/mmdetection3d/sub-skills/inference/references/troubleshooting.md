# Inference troubleshooting

## Command helper printed a command but did not run anything

That is expected. `scripts/build_inference_command.py` is a renderer, not a runner. It does not import MMDetection3D, download checkpoints, open a display, or use a GPU. Copy, inspect, and run the rendered command only when the user explicitly asks for execution.

## `--score-thr` vs `--pred-score-thr`

The v1.4.x demo CLIs use `--pred-score-thr`. Older examples may describe this as `--score-thr`. The bundled command helper accepts either spelling and renders `--pred-score-thr` for detection tasks.

For PGD-style monocular models, prediction scores are not necessarily in `[0, 1]`; a high threshold such as `8` can be intentional.

## No display, remote server, or Open3D window errors

Symptoms:

- `DISPLAY` is missing.
- `--show` opens no window or is forced off.
- LiDAR visualization files are missing even though predictions were saved.
- Open3D or GUI backend errors appear.

Action:

1. Omit `--show` on remote/headless hosts.
2. Keep `--out-dir` and keep prediction saving enabled.
3. Inspect `OUT_DIR/preds/*.json` first.
4. Use a local display or virtual display only if the user needs rendered LiDAR views.
5. Do not promise saved LiDAR/Open3D images when the run is headless; camera-image visualizations are more likely to save without an online LiDAR viewer.

## Config/checkpoint mismatch

Symptoms:

- Missing or unexpected keys while loading weights.
- Class names, palette, or label IDs look wrong.
- Inference output is empty or nonsensical after a successful load.
- Model construction errors mention unknown layers, heads, or registries.

Action:

1. Verify config and checkpoint come from the same model family and task.
2. Verify the dataset/classes in the config match the checkpoint metadata.
3. For project models, ensure project modules are importable before model construction.
4. If using an alias, remember that actual inference may download weights; use local files for reproducibility.
5. If changing config values with `cfg_options`, keep architecture and checkpoint-compatible fields intact.

## Device, CUDA, and backend errors

Symptoms:

- `torch.cuda.set_device` fails.
- MMCV ops, sparse-convolution ops, or custom CUDA ops are missing.
- CPU execution warns or fails for model components.
- Segmentation or voxel models fail during sparse convolution.

Action:

1. Prefer an explicit CUDA device such as `cuda:0` for full inference claims.
2. Use CPU only for limited debugging when the selected model path is known to tolerate it.
3. Match PyTorch, CUDA, MMCV, MMEngine, MMDetection, and MMDetection3D versions.
4. Check whether the config uses sparse backends such as spconv, MinkowskiEngine, TorchSparse, or project-specific ops.
5. If hardware or backend is unavailable, stop at command construction and report the blocked requirement.

## Checkpoint download or network failures

Symptoms:

- Alias initialization hangs or fails while resolving weights.
- URL checkpoint loading fails.
- Checkpoint path is missing after command construction.

Action:

1. Download checkpoints before the run and pass local paths.
2. Record which config/checkpoint pair was intended.
3. Avoid treating command-render success as model-readiness proof.
4. If network is restricted, ask the user for an accessible checkpoint file.

## Annotation/info file mismatch for monocular or multi-modality inference

Symptoms:

- Error text like `the info file of ... is not provided`.
- Key errors for `images`, `cam2img`, `lidar2cam`, `lidar2img`, `depth2img`, or the requested camera.
- Assertion failures from mismatched list lengths.
- Wrong camera view or saved visualization under an unexpected camera directory.

Action:

1. Load or inspect the info file and find the exact keys under `data_list[*]['images']`.
2. Pass that exact key as `cam_type` when using the Python inferencer.
3. Ensure the image basename matches the info record basename for that camera.
4. For list inputs to the inferencer, provide per-sample info files when required; each list item's `infos` file is expected to describe one sample.
5. For multi-modality inference, ensure point-cloud, image, and info records are aligned sample-by-sample.

Camera-key cautions:

- KITTI examples in this snapshot commonly use `CAM2` for demo/inferencer workflows.
- Other datasets may use keys such as `CAM_FRONT`, `CAM_BACK`, `CAM0`, or project-specific names.
- The info file is the source of truth.

## `--cam-type` does not appear to affect a demo run

For direct Python inferencer usage, pass `cam_type` to the inferencer call, for example:

```python
inferencer(dict(img='image.png', infos='infos.pkl'), cam_type='CAM2')
```

If a demo CLI run appears to ignore a camera override, switch to the Python inferencer workflow and pass `cam_type` explicitly. Also verify the info file contains the requested key and that the saved visualization path uses the expected camera directory.

## ndarray vs file-path limitations

File-path demos:

- Demo commands accept file paths only.
- They do not accept in-memory `numpy.ndarray` objects.

Low-level APIs:

- `inference_detector` supports point arrays by switching the loader to dictionary-based point loading.
- `inference_segmentor` is file-path oriented; loaded point arrays are not supported in the low-level function.
- Low-level monocular and multi-modality functions are safest with image file paths because they perform basename checks against the info file.

Inferencer classes:

- `LidarDet3DInferencer` supports point arrays and path inputs.
- `LidarSeg3DInferencer` supports point arrays and path inputs when dimensions match the config.
- `MonoDet3DInferencer` supports image arrays when the info file supplies camera matrices.
- `MultiModalityDet3DInferencer` supports point and image arrays when the info file supplies camera matrices.

If the user wants to batch two point clouds as arrays and compare with path inputs, use an inferencer class rather than a demo command.

## Multi-view and multi-modality limitations

Symptoms:

- Warnings about `LoadMultiViewImageFromFiles` not being supported.
- Assertions that point and image directory lengths differ.
- Missing camera entries when using `cam_type='all'`.
- Project model imports or CUDA ops fail.

Action:

1. Start with a validated single-view `LoadImageFromFile` config if possible.
2. Use `cam_type='all'` only after checking the model pipeline supports the expected directory/image mapping.
3. For directory inputs, confirm both point-cloud and image directories contain matching sample counts and ordering.
4. For BEVFusion-like or other project models, check project dependency and checkpoint requirements before promising execution.

## Output directory is empty

Possible causes:

- `out_dir` was empty.
- Both `no_save_vis` and `no_save_pred` were set, causing demos to suppress output.
- `no_save_pred` suppressed JSON output.
- LiDAR visualization required `show=True` and a display, but the run was headless.
- The command failed before model forward or postprocess.

Action:

1. Re-render or rerun with `--out-dir outputs`.
2. Do not set `--no-save-pred` unless the user only wants console output.
3. Inspect logs for model-load and forward errors before assuming no detections.
4. For camera workflows, look under `OUT_DIR/vis_camera/<cam_type>/`.
5. For predictions, look under `OUT_DIR/preds/`.

## Empty predictions with a successful run

Possible causes:

- Score threshold too high.
- Config/checkpoint do not match the sample dataset or class set.
- Point-cloud dimensions, coordinate mode, or image calibration do not match the model.
- The sample is genuinely out of distribution or contains no target objects.

Action:

1. Lower `pred_score_thr` for detection, accounting for model-specific score ranges.
2. Verify the point cloud has the expected number of features per point.
3. Verify the annotation/info file calibration matches the image and point cloud.
4. Try the model's known sample data and matching config/checkpoint pair before debugging custom data.

## When to stop and report a blocker

Stop instead of continuing to execute if:

- Required checkpoint cannot be obtained.
- No compatible CUDA/backend environment is available for a GPU-required model.
- The user cannot provide the info file needed for monocular or multi-modality inference.
- A selected project model requires uninstalled project-specific ops.
- The user requested only command construction, not actual model execution.
