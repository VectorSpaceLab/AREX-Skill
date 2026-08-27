# MMAction2 inference API reference

This reference captures the inference surfaces that are safe to use from an installed MMAction2 package. Examples use placeholders such as `CONFIG.py`, `CHECKPOINT.pth`, `INPUT.mp4`, and `classes.txt`; replace them with user-owned local files.

## Direct recognizer APIs

### `init_recognizer`

Verified signature:

```python
init_recognizer(
    config: Union[str, pathlib.Path, mmengine.Config],
    checkpoint: Optional[str] = None,
    device: Union[str, torch.device] = "cuda:0",
) -> torch.nn.Module
```

Behavior:

- `config` may be a string path, `pathlib.Path`, or `mmengine.Config` object.
- A non-path, non-`Config` value raises `TypeError` containing `config must be a filename or Config object`.
- If `checkpoint is None`, no checkpoint is loaded; this is the safest build-only path.
- If `checkpoint` is set, MMEngine loads it with `map_location="cpu"` before moving the model to `device`.
- The function attaches `model.cfg`, moves the model to the requested device, and calls `model.eval()`.
- The source default is `device="cuda:0"`; pass `device="cpu"` explicitly on CPU-only machines.

Safe build snippet:

```python
from mmengine import Config
from mmaction.apis import init_recognizer

cfg = Config.fromfile("CONFIG.py")
model = init_recognizer(cfg, checkpoint=None, device="cpu")
```

### `inference_recognizer`

Verified signature:

```python
inference_recognizer(
    model: torch.nn.Module,
    video: Union[str, dict],
    test_pipeline: Optional[mmengine.dataset.Compose] = None,
) -> ActionDataSample
```

Behavior:

- If `test_pipeline` is omitted, the function builds one from `model.cfg.test_pipeline`.
- A dict input is treated as already-packed pipeline input and passed through unchanged.
- A local string path ending in `.npy` is treated as audio feature input with keys `audio_path`, `total_frames=len(np.load(path))`, `start_index=0`, and `label=-1`.
- Any other existing local string path is treated as RGB video input with keys `filename`, `label=-1`, `start_index=0`, and `modality="RGB"`.
- Unsupported or non-existing values raise `RuntimeError` containing `The type of argument `video` is not supported`.
- Return type is `ActionDataSample`; the primary score tensor is `result.pred_score`.

Top-k snippet:

```python
from mmaction.apis import inference_recognizer

result = inference_recognizer(model, "INPUT.mp4")
scores = result.pred_score.detach().cpu()
values, indices = scores.topk(min(5, scores.numel()))
topk = list(zip(indices.tolist(), values.tolist()))
```

### `inference_skeleton`

Verified signature:

```python
inference_skeleton(
    model: torch.nn.Module,
    pose_results: List[dict],
    img_shape: Tuple[int],
    test_pipeline: Optional[mmengine.dataset.Compose] = None,
) -> ActionDataSample
```

Use this after pose estimation when the action recognizer expects pose/keypoint input. Each per-frame pose dict must include `keypoints` and `keypoint_scores`; the helper constructs the pose annotation with `modality="Pose"`, `total_frames`, `keypoint`, and `keypoint_score`, then delegates to `inference_recognizer`.

### `detection_inference`

Verified signature:

```python
detection_inference(
    det_config: Union[str, pathlib.Path, mmengine.Config, torch.nn.Module],
    det_checkpoint: str,
    frame_paths: List[str],
    det_score_thr: float = 0.9,
    det_cat_id: int = 0,
    device: Union[str, torch.device] = "cuda:0",
    with_score: bool = False,
) -> tuple
```

Behavior:

- Requires optional `mmdet` runtime APIs.
- `det_config` may also be an already-created detector model; in that case `det_checkpoint` may be `None`.
- Keeps boxes whose predicted class equals `det_cat_id` and whose score is greater than `det_score_thr`.
- Returns `(bbox_results, det_data_samples)`. Each bbox array has four columns, or five columns when `with_score=True`.

Exact missing-dependency error:

```text
Failed to import `inference_detector` and `init_detector` from `mmdet.apis`. These apis are required in this inference api! 
```

### `pose_inference`

Verified signature:

```python
pose_inference(
    pose_config: Union[str, pathlib.Path, mmengine.Config, torch.nn.Module],
    pose_checkpoint: str,
    frame_paths: List[str],
    det_results: List[np.ndarray],
    device: Union[str, torch.device] = "cuda:0",
) -> tuple
```

Behavior:

- Requires optional `mmpose` runtime APIs.
- `pose_config` may also be an already-created pose model; in that case `pose_checkpoint` may be `None`.
- Runs top-down pose on each frame and detector box.
- Returns `(pose_results, pose_data_samples)`. Pose dicts include keys such as `keypoints`, `keypoint_scores`, `bboxes`, and `bbox_scores`.

Exact missing-dependency error:

```text
Failed to import `inference_topdown` and `init_model` from `mmpose.apis`. These apis are required in this inference api! 
```

## High-level inferencers

### `ActionRecogInferencer`

Verified constructor signature:

```python
ActionRecogInferencer(
    model: Union[dict, mmengine.Config, mmengine.ConfigDict, str],
    weights: Optional[str] = None,
    device: Optional[str] = None,
    label_file: Optional[str] = None,
    input_format: str = "video",
    pack_cfg: dict = {},
    scope: Optional[str] = "mmaction",
) -> None
```

Important call options:

```python
inferencer(
    inputs,
    return_datasamples=False,
    batch_size=1,
    return_vis=False,
    show=False,
    wait_time=0,
    draw_pred=True,
    vid_out_dir="",
    out_type="video",
    print_result=False,
    pred_out_file="",
    target_resolution=None,
)
```

Input formats:

| `input_format` | Input value | Packing behavior |
| --- | --- | --- |
| `"video"` | Local video path string | Inserts/uses `DecordInit` and `DecordDecode`; requires Decord for the default pipeline. |
| `"rawframes"` | Directory path string | Counts files matching `filename_tmpl`, then uses `RawFrameDecode`; default template is `img_{:05}.jpg`, modality `RGB`, start index `1`. |
| `"array"` | 4D `np.ndarray` | Uses `ArrayDecode`; last channel dimension `3` means RGB and `2` means optical flow. |
| `"dict"` | Already-packed dict | Supported by the pack transform but usually accessed through low-level APIs or custom pipelines. |

Pipeline adjustments made by the inferencer:

- Video input rewrites decode transforms to Decord-based transforms.
- Rawframes input rewrites decode transforms to raw-frame decoding and removes video initialization transforms.
- Array input rewrites decode transforms to array decoding and removes initialization transforms.
- Test-time multi-crop transforms `ThreeCrop` and `TenCrop` are replaced by `CenterCrop`.
- For `Recognizer3D`, `SampleFrames.num_clips` is set to `1` to reduce memory use.

Result shape:

- Default `return_datasamples=False`: returns a dict with `predictions` and `visualization`.
- Each prediction dict contains `pred_labels` and `pred_scores`.
- `pred_out_file` dumps the result dict; use the default serializable prediction mode for dumps.

### `MMAction2Inferencer`

Verified constructor signature:

```python
MMAction2Inferencer(
    rec: Optional[str] = None,
    rec_weights: Optional[str] = None,
    device: Optional[str] = None,
    label_file: Optional[str] = None,
    input_format: str = "video",
) -> None
```

Verified call signature:

```python
mmaction2(inputs, batch_size=1, **kwargs) -> dict
```

Behavior:

- `rec` is required. Omitting it raises `ValueError` containing `rec algorithm should provided.`
- `rec` may be a short model alias, a full model/config name known to the installed metadata, or a local config path.
- Source examples and tests cover short aliases such as `tsn`; the class docstring also documents aliases such as `slowfast`.
- `rec_weights` is the local checkpoint override. If it is omitted while `rec` is a metadata model name, the inferencer may try to resolve metadata weights; avoid this in offline smoke checks.
- Returns a dict with `predictions` and `visualization`.
- Prediction entries contain `rec_labels` and `rec_scores`, each nested by recognition task.

Example:

```python
from mmaction.apis.inferencers import MMAction2Inferencer

inferencer = MMAction2Inferencer(
    rec="CONFIG.py",          # or a model alias/name known to the installed package
    rec_weights="CHECKPOINT.pth",  # omit only when random-weight smoke is acceptable
    device="cpu",
    label_file="classes.txt",
)
results = inferencer(
    "INPUT.mp4",
    print_result=True,
    pred_out_file="predictions.json",
    vid_out_dir="visualized",
    out_type="video",
)
```

## Labels and prediction files

- Recognition `label_file` is read as one class name per line and attached to the visualizer metadata.
- Direct API users should map `result.pred_score` indices to labels themselves.
- `ActionRecogInferencer` prediction dict keys are `pred_labels` and `pred_scores`.
- `MMAction2Inferencer` prediction dict keys are `rec_labels` and `rec_scores`.
- `pred_out_file` writes via MMEngine serialization; prefer `.json`, `.yaml`/`.yml`, or `.pkl` according to the consuming workflow.

## Device guidance

- Use `device="cpu"` for portable build and inference smoke checks.
- Use `device="cuda:0"` or another CUDA device only after the runtime proves a CUDA-enabled PyTorch/MMCV stack and visible GPU.
- `init_recognizer`, `detection_inference`, and `pose_inference` default to `"cuda:0"`; pass CPU explicitly when needed.
- `MMAction2Inferencer(device=None)` asks the underlying inferencer to choose an available device, but explicit CPU is more predictable for verification.
