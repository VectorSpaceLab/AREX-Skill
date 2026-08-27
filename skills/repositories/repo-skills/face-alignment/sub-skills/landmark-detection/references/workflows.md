# Landmark Detection Workflows

## Purpose

Read this when you want to run `FaceAlignment` on a single image, a batch tensor, or a directory of images.

## Quick smoke helper

The bundled helper prints a JSON summary without plotting:

```bash
python scripts/detect_landmarks.py --input /path/to/image.jpg --device cpu --landmarks-type 2d
```

For a directory:

```bash
python scripts/detect_landmarks.py --input /path/to/images --device cpu --landmarks-type 3d
```

## Single-image workflow

Use `get_landmarks_from_image` when you already have one image path or array.

```python
import face_alignment

fa = face_alignment.FaceAlignment(
    face_alignment.LandmarksType.THREE_D,
    device='cpu',
    face_detector='sfd',
    compile=False,
)
landmarks = fa.get_landmarks_from_image('path/to/image.jpg')
```

Notes:

- `get_landmarks` is a deprecated alias for `get_landmarks_from_image`.
- Pass `return_bboxes=True` or `return_landmark_score=True` if you need the detector boxes or per-point scores back.
- The default `device` in the class constructor is `cuda`, so CPU-only users should set `device='cpu'` explicitly.

## Batch workflow

Use `get_landmarks_from_batch` when you already have a tensor batch in `B, C, H, W` order.

```python
import numpy as np
import torch
import face_alignment
from face_alignment.utils import get_image

fa = face_alignment.FaceAlignment(
    face_alignment.LandmarksType.TWO_D,
    device='cpu',
    compile=False,
)
image = get_image('path/to/image.jpg')
batch = np.stack([image, image])
batch = torch.Tensor(batch.transpose(0, 3, 1, 2))
preds = fa.get_landmarks_from_batch(batch)
```

Notes:

- The method returns one landmark list per batch element.
- Use `max_batch_size` to chunk many detected faces on memory-constrained hosts.
- If your batch contains images with no faces, the corresponding list entry will be empty.

## Directory workflow

Use `get_landmarks_from_directory` when you want to scan a directory tree.

```python
import face_alignment

fa = face_alignment.FaceAlignment(
    face_alignment.LandmarksType.TWO_HALF_D,
    device='cpu',
    compile=False,
)
predictions = fa.get_landmarks_from_directory(
    '/path/to/images',
    extensions=['.jpg', '.png'],
    recursive=True,
    show_progress_bar=True,
)
```

Notes:

- The default extensions are `['.jpg', '.png']`.
- The directory scan is recursive by default.
- The result is a dictionary keyed by image path.

## Configuration tips

- Use `flip_input=True` for a small accuracy boost at the cost of extra compute.
- Use `compile=False` if `torch.compile` is slow, unavailable, or not worth the first-run delay.
- Use a small `max_batch_size` when many faces appear in a single image.
- If you already have detector boxes, pass them as `detected_faces` to skip detection.

## Output contract

- `None` means no faces were found and you did not request extra return values.
- When you request extra outputs, the API returns a 3-tuple: `(landmarks, landmark_scores, detected_faces)`.
- 2D and 2.5D landmarks have shape `(68, 2)`.
- 3D landmarks have shape `(68, 3)`.
