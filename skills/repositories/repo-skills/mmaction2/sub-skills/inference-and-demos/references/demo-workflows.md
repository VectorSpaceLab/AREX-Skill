# MMAction2 inference and demo-style workflows

Use these workflows from an installed MMAction2 runtime. They are designed to avoid source-checkout assumptions: every file path is a placeholder for a user-owned local config, checkpoint, input, label file, or output directory.

## 1. Build-only validation with no checkpoint download

Use this before attempting a real media forward pass:

```bash
python scripts/mmaction2_inference_smoke.py \
  --config CONFIG.py \
  --device cpu \
  --check-build-only
```

Expected validation:

- Imports `mmaction` and core inference APIs.
- Parses `CONFIG.py` with MMEngine.
- Builds the recognizer through `init_recognizer(config, checkpoint=None, device="cpu")`.
- Does not load or download weights.

To inspect the available API signatures without building a model:

```bash
python scripts/mmaction2_inference_smoke.py --print-signatures
```

## 2. Direct RGB/video recognition API

Use this when the user needs a raw `ActionDataSample` and direct access to `pred_score`.

```python
from mmengine import Config
from mmaction.apis import inference_recognizer, init_recognizer

cfg = Config.fromfile("CONFIG.py")
model = init_recognizer(cfg, checkpoint="CHECKPOINT.pth", device="cpu")
result = inference_recognizer(model, "INPUT.mp4")

scores = result.pred_score.detach().cpu()
values, indices = scores.topk(min(5, scores.numel()))
print(list(zip(indices.tolist(), values.tolist())))
```

If the user has no checkpoint and only wants to validate construction and the decode/pipeline path, set `checkpoint=None`; scores will be random and must not be interpreted as a real model prediction.

## 3. High-level action recognition inferencer

Use `ActionRecogInferencer` when the user needs consistent prediction dicts, label-file metadata, visualization output, rawframe or array input, or a batch-size option.

```python
from mmaction.apis.inferencers import ActionRecogInferencer

inferencer = ActionRecogInferencer(
    model="CONFIG.py",
    weights="CHECKPOINT.pth",
    device="cpu",
    label_file="classes.txt",
    input_format="video",
)
results = inferencer(
    "INPUT.mp4",
    batch_size=1,
    print_result=True,
    pred_out_file="predictions.json",
    vid_out_dir="visualized",
    out_type="video",
    show=False,
)
print(results["predictions"][0]["pred_labels"])
print(results["predictions"][0]["pred_scores"])
```

Notes:

- `classes.txt` is one class label per line for action-recognition visualization.
- If `vid_out_dir=""`, `show=False`, and `return_vis=False`, no visualization is produced.
- For headless servers, keep `show=False` and write to `vid_out_dir`, or set `return_vis=True` to receive frames in memory.
- If exact validation-time multi-crop/TTA behavior matters, route to the train/test skill; the inferencer intentionally simplifies the test pipeline for memory safety.

## 4. Unified `MMAction2Inferencer` wrapper

Use this for demo-like recognition runs where `rec` identifies the recognition model and `rec_weights` supplies the checkpoint.

```python
from mmaction.apis.inferencers import MMAction2Inferencer

mmaction2 = MMAction2Inferencer(
    rec="CONFIG.py",             # local config path, short alias, or known model/config name
    rec_weights="CHECKPOINT.pth", # local checkpoint; omit only for metadata lookup or random-weight smoke
    device="cpu",
    label_file="classes.txt",
    input_format="video",
)
results = mmaction2(
    "INPUT.mp4",
    batch_size=1,
    print_result=True,
    pred_out_file="predictions.json",
    vid_out_dir="visualized",
    out_type="gif",
    show=False,
)
print(results["predictions"][0]["rec_labels"])
print(results["predictions"][0]["rec_scores"])
```

Offline rule: prefer `rec="CONFIG.py"` plus a local `rec_weights` path. Short aliases such as `tsn` are convenient, but aliases or full model names may try to resolve packaged metadata weights if `rec_weights` is omitted.

## 5. Rawframe-folder input

Use `ActionRecogInferencer` when the user's input is a directory of extracted frames.

```python
from mmaction.apis.inferencers import ActionRecogInferencer

inferencer = ActionRecogInferencer(
    model="CONFIG.py",
    weights="CHECKPOINT.pth",
    device="cpu",
    input_format="rawframes",
    pack_cfg={
        "filename_tmpl": "img_{:05}.jpg",  # adjust if user frames use another pattern
        "modality": "RGB",
        "start_index": 1,
    },
)
results = inferencer("FRAME_DIR", pred_out_file="predictions.json")
```

Validation checks:

- The frame directory contains files matching the template.
- `modality="Flow"` expects flow-style frame pairs and a compatible config.
- If the user only has a video file, do not route through rawframes unless frames have already been extracted.

## 6. Decoded array input

Use `input_format="array"` when a caller already decoded frames.

```python
import numpy as np
from mmaction.apis.inferencers import ActionRecogInferencer

frames: np.ndarray = load_user_frames_somehow()  # shape: T x H x W x C
inferencer = ActionRecogInferencer(
    model="CONFIG.py",
    weights="CHECKPOINT.pth",
    device="cpu",
    input_format="array",
)
results = inferencer(frames, return_vis=False, print_result=True)
```

Array rules:

- Last channel dimension `3` is treated as RGB.
- Last channel dimension `2` is treated as optical flow.
- Make sure the config pipeline and model family match the modality.

## 7. Audio-feature `.npy` inference

Use the direct recognizer API for audio-feature configs. The low-level input dispatcher treats an existing `.npy` path as audio features.

```python
from mmengine import Config
from mmaction.apis import inference_recognizer, init_recognizer

cfg = Config.fromfile("AUDIO_CONFIG.py")
model = init_recognizer(cfg, checkpoint="AUDIO_CHECKPOINT.pth", device="cpu")
result = inference_recognizer(model, "AUDIO_FEATURE.npy")
print(result.pred_score)
```

Validation checks:

- The selected config is an audio-recognition config whose test pipeline expects `audio_path` and audio feature transforms.
- The `.npy` file exists and has the feature shape expected by that config.
- Do not interpret results if running without a trained audio checkpoint.

## 8. Manual label mapping from `pred_score`

For direct API outputs, map class IDs yourself:

```python
labels = [line.strip() for line in open("classes.txt", encoding="utf-8")]
scores = result.pred_score.detach().cpu()
values, indices = scores.topk(min(5, len(labels), scores.numel()))
for class_id, score in zip(indices.tolist(), values.tolist()):
    label = labels[class_id] if class_id < len(labels) else f"class_{class_id}"
    print(f"{class_id}: {label}: {score:.4f}")
```

For spatio-temporal detection label maps, expect `label_id: label_name` style files and parse them separately from one-label-per-line recognition class lists.

## 9. Headless visualization outputs

Recommended options:

- Use `show=False` on servers, notebooks without GUI display, SSH sessions, and CI.
- Use `vid_out_dir="visualized"` to save rendered videos or GIFs.
- Use `out_type="video"` for video files or `out_type="gif"` for GIFs.
- Use `target_resolution=(width, height)` to resize output; `-1` may be used by visualizer-style APIs to preserve aspect ratio where supported.
- Use `return_vis=True` only when the caller wants visualization frames in memory.

If you use the direct API rather than an inferencer, create an `ActionVisualizer`, set `visualizer.dataset_meta={"classes": labels}`, and call `add_datasample(..., draw_pred=True, show_frames=False, out_path="OUTPUT.mp4", out_type="video")`.

## 10. Skeleton recognition path

This path requires local detector, pose, and skeleton-action configs/checkpoints plus optional `mmdet` and `mmpose` installations.

```python
from mmaction.apis import (
    detection_inference,
    inference_skeleton,
    init_recognizer,
    pose_inference,
)

# frame_paths: list[str] extracted from the user's video
# img_shape: (height, width) of the original frames

det_bboxes, _ = detection_inference(
    det_config="DET_CONFIG.py",
    det_checkpoint="DET_CHECKPOINT.pth",
    frame_paths=frame_paths,
    det_score_thr=0.9,
    det_cat_id=0,
    device="cpu",
)
pose_results, pose_samples = pose_inference(
    pose_config="POSE_CONFIG.py",
    pose_checkpoint="POSE_CHECKPOINT.pth",
    frame_paths=frame_paths,
    det_results=det_bboxes,
    device="cpu",
)
model = init_recognizer("SKELETON_CONFIG.py", "SKELETON_CHECKPOINT.pth", device="cpu")
result = inference_skeleton(model, pose_results, img_shape)
```

Validation checks:

- `mmdet` and `mmpose` import successfully before running the staged pipeline.
- Detector class ID `0` means the default human category for common COCO-style detectors; change only if the detector uses a different label map.
- `pose_results` entries contain `keypoints` and `keypoint_scores`.
- The skeleton label map matches the skeleton action checkpoint, not the detector or pose model.

## 11. Spatio-temporal action detection path

Use this when the user asks for per-person action labels over time rather than a single clip-level action label.

High-level sequence:

1. Extract frames from the user's video into a temporary working directory.
2. Choose center timestamps based on the action-detection config's clip length and frame interval.
3. Run `detection_inference` on center frames to produce human proposals.
4. Build the spatio-temporal action model from the action-detection config and local checkpoint.
5. For each timestamp, prepare a clip tensor and `ActionDataSample` with `proposals=InstanceData(bboxes=proposal)`.
6. Run the model in predict mode, threshold per-action scores, map label IDs, and draw boxes/labels onto output frames.

Safety notes:

- This path is more expensive and less portable than clip-level recognition.
- It needs optional detector dependencies and a compatible action-detection checkpoint.
- Use local checkpoints; do not rely on remote checkpoint URLs for production smoke checks.
- If the user wants to train or evaluate an AVA-style detector rather than run inference, route to the train/test and data/config sub-skills.
