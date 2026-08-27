# Extractor and feature-schema troubleshooting

Use this when extractor construction, `.extract()`, or precomputed feature validation fails before a complete image-pair matching workflow.

| Symptom | Likely cause | Fix |
|---|---|---|
| `AttributeError: module 'cv2' has no attribute 'SIFT_create'` or OpenCV SIFT is unavailable | The installed OpenCV build does not expose SIFT. Modern `opencv-python` usually includes SIFT, but older/conflicting builds may not. | Upgrade to a current OpenCV package, or use a compatible `opencv-contrib-python` build. Avoid keeping conflicting OpenCV wheels installed together. If OpenCV SIFT remains unavailable, use a verified `pycolmap` SIFT backend or choose a learned extractor if weight downloads are allowed. |
| `ImportError: Cannot find module pycolmap` when constructing `SIFT(backend='pycolmap...')` | `pycolmap` is optional and is not part of the base runtime dependencies. | Use `backend='opencv'` for the default offline-safe path, or install `pycolmap` intentionally for the target environment. |
| Warning about buggy pycolmap CPU SIFT in versions `< 0.5.0` | The SIFT backend is using pycolmap CPU behavior that the implementation warns is buggy. | Upgrade pycolmap, use a verified CUDA-capable pycolmap build when hardware supports it, or fall back to OpenCV SIFT. Treat old pycolmap CPU results as unverified. |
| `pycolmap_cuda` requested but CUDA is unavailable or pycolmap has no CUDA support | `pycolmap_cuda` requires both visible CUDA hardware and a pycolmap build with CUDA support. | Probe hardware and pycolmap capabilities first. Use `backend='opencv'` or `backend='pycolmap_cpu'` when CUDA is unavailable, but keep the CPU pycolmap version caveat in mind. |
| Neural extractor construction hangs or fails on a network/cache error | `SuperPoint`, `DISK`, `ALIKED`, `DoGHardNet`, and feature-specific LightGlue matchers can download pretrained weights on first use. | For offline schema checks, use `SIFT(backend='opencv')`. If neural features are required, pre-populate the relevant torch/Kornia cache or allow network access. Surface the first-use download to the user instead of hiding it. |
| `ValueError: max_num_keypoints must be positive or None` | `SuperPoint` rejects zero and negative `max_num_keypoints`. | Use a positive integer such as `1024`, or `None` to keep all detected SuperPoint keypoints. |
| SIFT/OpenCV construction fails after setting `max_num_keypoints=None` | OpenCV SIFT expects a numeric feature limit in this wrapper. | Use the SIFT default, a positive integer, or a backend-specific tested configuration. Reserve `None` mainly for SuperPoint/DISK all-keypoint behavior. |
| ALIKED does not return exactly the requested number of keypoints | With `detection_threshold > 0`, ALIKED is in threshold mode and `max_num_keypoints` acts as a cap, not exact top-k. | For exact top-k behavior, set `detection_threshold <= 0` and `max_num_keypoints` to a positive integer, for example `ALIKED(max_num_keypoints=1024, detection_threshold=-1)`. |
| Descriptor dimension assertion fails in `LightGlue` | The selected matcher preset expects a different descriptor dimension. | Pair `superpoint` with 256-D descriptors, `disk`/`aliked`/`sift`/`doghardnet` with 128-D descriptors. Do not use `ALIKED(model_name='aliked-t16')` with `LightGlue(features='aliked')` because that variant emits 64-D descriptors. |
| `KeyError: 'scales'` or `KeyError: 'oris'` with SIFT/DoGHardNet matcher | `LightGlue(features='sift')` and `LightGlue(features='doghardnet')` set `add_scale_ori=True`; precomputed features are missing scale/orientation fields. | Include `scales` and `oris` shaped `[B,N]`, with orientations in radians, or recompute features using `SIFT(...).extract(image)` / `DoGHardNet(...).extract(image)`. |
| Matching code sees descriptors shaped `[B,D,N]` | Some feature pipelines store descriptors channel-first. LightGlue expects `[B,N,D]`. | Transpose descriptors to `[B,N,D]` and keep keypoints/descriptors aligned by the same `N` order. |
| Keypoints appear shifted or normalized incorrectly | Missing/wrong `image_size`, or `(height,width)` was supplied instead of `(width,height)`. | Set `image_size` to `[width,height]` for each image. If using `.extract()`, keep its emitted `image_size`. |
| Grayscale/RGB shape or range errors | Input tensor shape/range does not match extractor expectations. | Use tensors shaped `(C,H,W)` or `(1,C,H,W)`, float in `[0,1]`. `load_image` returns RGB `(3,H,W)`. SuperPoint, SIFT, and DoGHardNet convert RGB to grayscale internally; DISK and ALIKED convert grayscale to RGB internally. |
| `.extract()` assertion fails for a batch larger than one | The shared helper is designed for one image at a time and asserts `B=1`. | Call `.extract()` per image, or call lower-level extractor `forward` only if you handle preprocessing, image sizes, padding, and batching yourself. |
| SIFT image returns zero or very few keypoints | Low-texture image, aggressive resize, high detection threshold, or small `max_num_keypoints`. | Try `resize=None` or a larger resize, lower `detection_threshold`, inspect the image range, and verify the image is readable. Zero-keypoint cases are valid but will produce no matches. |
| DoGHardNet construction fails in a minimal environment | DoGHardNet uses SIFT detections plus Kornia HardNet descriptor components, which may require weights/cache and compatible Kornia/torch behavior. | Use SIFT for offline validation; only choose DoGHardNet when HardNet weights can be downloaded/cached and the environment has the required runtime dependencies. |

## Fast diagnosis commands

Offline-safe schema inspection with OpenCV SIFT:

```bash
python scripts/inspect_feature_schema.py --image path/to/image.jpg --extractor sift --max-keypoints 512 --device cpu
```

Neural extractor inspection, acknowledging first-use downloads:

```bash
python scripts/inspect_feature_schema.py --image path/to/image.jpg --extractor aliked --aliked-model aliked-n16 --max-keypoints 1024 --detection-threshold -1
```

Use the first command when the user's immediate problem is feature dictionary shape or missing SIFT-family fields and network access is uncertain.
