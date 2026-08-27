# API Reference

## Purpose

Read this when you need exact signatures, return shapes, or helper-function behavior for the installed `face_alignment` package.

## Verified public surface

### `FaceAlignment`

Constructor signature:

```python
FaceAlignment(
    landmarks_type,
    network_size=NetworkSize.LARGE,
    device='cuda',
    dtype=torch.float32,
    flip_input=True,
    face_detector='sfd',
    face_detector_kwargs=None,
    verbose=False,
    compile=True,
    max_batch_size=1,
)
```

Notes:

- `landmarks_type` must be one of `LandmarksType.TWO_D`, `LandmarksType.TWO_HALF_D`, or `LandmarksType.THREE_D`.
- `get_landmarks` is a deprecated alias for `get_landmarks_from_image`.
- The default device is `cuda`; CPU-only usage should pass `device='cpu'` explicitly.
- `compile=True` applies `torch.compile` and warms the model once. Use `compile=False` when you want fast startup or simpler smoke behavior.

### Landmark methods

```python
get_landmarks_from_image(image_or_path, detected_faces=None, return_bboxes=False, return_landmark_score=False)
get_landmarks_from_batch(image_batch, detected_faces=None, return_bboxes=False, return_landmark_score=False)
get_landmarks_from_directory(path, extensions=['.jpg', '.png'], recursive=True, show_progress_bar=True, return_bboxes=False, return_landmark_score=False)
```

Return contracts:

- `get_landmarks_from_image` returns a list of per-face landmark arrays, or `None` when no face is detected and no extra return values are requested.
- With `return_bboxes=True` or `return_landmark_score=True`, the methods return a 3-tuple: `(landmarks, landmark_scores, detected_faces)`.
- 2D and 2.5D landmarks are shaped `(68, 2)`.
- 3D landmarks are shaped `(68, 3)`.
- Batch outputs are lists of per-image landmark lists.
- Directory outputs are dictionaries keyed by image path.

Input notes:

- `image_or_path` accepts a string path, a NumPy array, or a torch tensor.
- `image_batch` expects a torch tensor with shape `B, C, H, W`.
- `get_landmarks_from_directory` scans only the extensions you pass; an empty extension list is invalid.

### Enumerations

```python
LandmarksType.TWO_D      # 1
LandmarksType.TWO_HALF_D # 2
LandmarksType.THREE_D    # 3

NetworkSize.LARGE        # 4
```

## Helper functions from `face_alignment.utils`

### Image and geometry helpers

```python
get_image(image_or_path)
flip(tensor, is_label=False)
draw_gaussian(image, point, sigma)
get_preds_fromhm(hm, center=None, scale=None)
create_target_heatmap(target_landmarks, centers, scales)
create_bounding_box(target_landmarks, expansion_factor=0.0)
```

What they do:

- `get_image` normalizes a path, NumPy array, or tensor into an RGB image array.
- `flip` mirrors images or heatmaps left-right.
- `draw_gaussian` writes a gaussian blob into a heatmap.
- `get_preds_fromhm` returns heatmap argmax coordinates, original-frame coordinates, and confidence scores.
- `create_target_heatmap` builds training-style landmark heatmaps.
- `create_bounding_box` computes a bounding box around landmark batches.

## Backend references

Detailed detector constructor signatures, backend dependencies, and device notes live in `sub-skills/detectors/references/detector-overview.md`.
