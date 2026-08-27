# RF-DETR Inference Troubleshooting

Use this guide for prediction, model selection, checkpoint loading, output interpretation, streaming, and inference optimization failures.

## Import and installation failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'rfdetr'` | Package not installed in the active Python environment. | `pip install rfdetr` in the environment that will run inference. |
| Import succeeds but Plus class access raises `ImportError` | `rfdetr_plus` is not installed or Plus dependencies/license requirements are not satisfied. | Install with `pip install "rfdetr[plus]"`; preserve the Plus license/account boundary. |
| `ModuleNotFoundError` for `supervision`, `torch`, `torchvision`, or `transformers` | Broken or incomplete base install. | Reinstall the base package; do not install training/export extras just to fix core inference unless those workflows are needed. |
| Importing removed legacy modules such as `rfdetr.util` or `rfdetr.deploy` fails | Those aliases were removed and now emit migration hints. | Use current `rfdetr.utilities` or export APIs through the export sibling route. |

Run the bundled inspector to check importability without downloads:

```bash
python scripts/inspect_rfdetr_models.py
python scripts/inspect_rfdetr_models.py --json
```

## Pretrained weight downloads and cache issues

Model construction with default `pretrain_weights` may download official weights if they are not cached. Prediction snippets that instantiate `RFDETRSmall()` or another pretrained class are therefore network/cache sensitive.

Remedies:

- For offline API inspection only, use the bundled inspector instead of constructing a model.
- For offline random-weight smoke checks, instantiate with `pretrain_weights=None` and understand accuracy will be random.
- Set `RF_HOME` or `ROBOFLOW_HOME` to choose a public model-cache directory when needed.
- If a cached official weight file has a wrong checksum, RF-DETR warns and does not overwrite automatically; explicitly re-download only after confirming the file is not a custom checkpoint you need.

## Checkpoint loading failures

| Symptom | Meaning | Fix |
| --- | --- | --- |
| `FileNotFoundError` or directory read error | The checkpoint path is missing or points at a directory. | Pass the actual `.pth`/`.ckpt` file. |
| `KeyError: 'args'` | The file is not an RF-DETR-style checkpoint. | Verify the checkpoint producer; instantiate a class directly only if you know the architecture and checkpoint format. |
| `Could not infer model class` | `model_name`, `pretrain_weights`, and filename lack a recognizable RF-DETR variant token. | Rename only if the file truly matches a known variant, or instantiate the exact variant class and pass `pretrain_weights=...`. |
| Error mentions `trust_checkpoint=True` | Safe deserialization rejected custom Python objects. | Use `trust_checkpoint=True` only for fully trusted checkpoint sources. |
| Plus checkpoint raises `ImportError` | Checkpoint is for Plus detection XL/2XL and the Plus package is unavailable. | Install `rfdetr[plus]` and satisfy Plus requirements; do not load it as core Large. |
| Fine-tuned labels are wrong | Code indexed `COCO_CLASSES` or a custom list directly by `class_id`. | Read `predictions.data["class_name"]`. |

Security rule: never set `trust_checkpoint=True` for an arbitrary downloaded or user-supplied file just to make loading proceed.

## Shape, patch size, and resolution errors

Typical messages mention `shape`, `patch_size`, `num_windows`, `block_size`, or `default resolution`.

Diagnosis:

1. Confirm `shape` is `(height, width)`.
2. Confirm both values are positive integers, not floats or booleans.
3. Confirm both dimensions are divisible by the model block size:
   - detection Nano/Small/Medium/Large: 32;
   - deprecated Base: 56;
   - segmentation Nano: 12;
   - other segmentation sizes and keypoint preview: 24.
4. Omit `patch_size` unless you are validating against a known architectural value. A supplied `patch_size` must match `model_config.patch_size`.
5. If `model.inference(compile=True)` was used, predict with the same optimized square resolution and batch size, or remove/rebuild the optimized model.
6. If `inference(inplace=True)` was used, create a new RF-DETR instance to change resolution or batch assumptions.

## Image input errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Tensor input error says pixel values are above 1 or below 0 | Tensor is not normalized to `[0, 1]`. | Divide uint8 image tensors by 255 before passing them. |
| Tensor channel-count error | Tensor is not `(C, H, W)` or `C` does not match model config. | For automatic RGB conversion, pass a PIL image or file path; for tensors, explicitly convert and reorder. |
| Local path starting with `http...` behaves unexpectedly | Only strings with URL schemes `http` or `https` are fetched. | Use valid local paths for files and real `http://`/`https://` URLs for remote images. |
| HTTP prediction hangs or raises HTTP error | Remote source unavailable or returns non-2xx. | Prefer local files for robust jobs; download separately with retry policy if needed. |

## Label and class-name mistakes

Problem pattern:

```python
labels = [COCO_CLASSES[class_id] for class_id in detections.class_id]
```

This is only safe for COCO-pretrained checkpoints with valid sparse COCO category IDs. It is wrong for many fine-tuned checkpoints and can also fail on COCO category gaps.

Safe pattern:

```python
labels = list(detections.data["class_name"])
```

For keypoints:

```python
labels = list(key_points.data["class_name"])
```

Interpretation rules:

- `"__background__"` can appear for no-object/background slots in fine-tuned or keypoint schemas.
- Empty string means RF-DETR encountered an unmapped class ID; check checkpoint/class schema.
- COCO pretrained class ID `90` is valid (`"toothbrush"`), not background.

## Keypoint-specific issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Expected `Detections` but got `KeyPoints` | Keypoint model returns `supervision.KeyPoints`. | Use keypoint fields or call `key_points.as_detections()` when only boxes are needed. |
| `K` is not 17 | Fine-tuned checkpoint uses custom keypoint schema. | Read `key_points.xy.shape[1]`; do not hard-code 17 except for the COCO preview checkpoint. |
| Annotator draws too many low-quality joints | `visible` defaults to `keypoint_confidence > 0`. | Apply a confidence threshold and set `key_points.visible` manually. |
| Class names shifted by one | Legacy background-first keypoint checkpoint. | Use `key_points.data["class_name"]`; inspect `num_keypoints_per_class` if debugging schema. |
| Missing covariance | The model/output did not include precision parameters or source shape. | Check for `"covariance" in key_points.data` before ellipse visualization. |

## Segmentation-specific issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `detections.mask` is `None` unexpectedly | Wrong model family or output was converted incorrectly. | Use `RFDETRSeg*` classes and keep the returned `Detections` object intact. |
| High memory while upsampling masks | Many detections at large source resolution. | Raise `threshold`, reduce input/source resolution, disable `include_source_image`, or process fewer frames per batch. |
| Empty detections but mask field still exists | Normal API contract. | Handle zero-length `Detections`; do not treat present mask storage as a positive detection. |

## Video, webcam, and RTSP failures

Checklist:

- `cv2.VideoCapture(source).isOpened()` must be true before entering the loop.
- OpenCV frames are BGR; convert to RGB before `model.predict(frame_rgb, ...)`.
- For display with OpenCV, annotate/display BGR frames consistently.
- `read()` can fail transiently for streams; decide outside RF-DETR whether to reconnect, skip, or stop.
- Use `include_source_image=False` in long loops to avoid accumulating frame copies.
- Avoid re-instantiating the model inside the frame loop.

## Device and memory optimization failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Warning that model is not optimized for inference | `predict()` is using the unoptimized module. | For latency-sensitive GPU inference, call `model.inference(dtype="float16")` after loading. |
| `inference(inplace=True)` with `compile=True` raises | In-place optimization requires `compile=False`. | Use `model.inference(compile=False, inplace=True, dtype="float16")`. |
| Cannot export/deploy/reinitialize after in-place optimization | In-place path cleared the original module. | Create or reload a new RF-DETR instance. |
| Resolution mismatch after optimization | Optimized snapshot was built for a different square resolution. | Remove non-inplace optimized model or recreate model after in-place optimization. |
| Batch-size mismatch after `compile=True` | JIT trace was compiled for a fixed batch size. | Re-run `model.inference(batch_size=new_size)` for non-inplace models, or reload for in-place models. |
| CPU/GPU copy still occurs for CUDA tensor input | `include_source_image=True` copies the tensor back to CPU for source storage. | Set `include_source_image=False`. |
