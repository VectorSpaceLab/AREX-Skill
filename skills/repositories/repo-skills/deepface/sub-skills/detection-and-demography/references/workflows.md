# Detection And Demography Workflows

## Extract Faces

```python
from deepface import DeepFace
faces = DeepFace.extract_faces("group.jpg", detector_backend="opencv", align=True, color_face="rgb")
for face in faces:
    print(face["facial_area"], face["confidence"])
```

Use `color_face="bgr"` when passing extracted faces to OpenCV-heavy code. Use `normalize_face=False` when the next consumer expects raw pixel values.

## Handle No-Face Images

With `enforce_detection=False`, DeepFace can return the full image region with confidence `0`. This is useful for robust pipelines but should not be reported as successful detection.

## Analyze Selected Demographics

```python
attrs = DeepFace.analyze("portrait.jpg", actions=["age", "gender"], detector_backend="opencv", silent=True)
```

Request only the actions needed. Demography models may download weights on first use.

## Batch Inputs

Both `extract_faces` and `analyze` accept lists of paths/arrays or 4D NumPy arrays. Batch results are nested: one list of face dictionaries per input image.

## Detector Fallback Decision Tree

1. Start with `opencv` for lightweight CPU checks.
2. If quality is insufficient and optional packages are installed, try `retinaface` or `mtcnn`.
3. If the image is already tightly cropped, use `skip` and route recognition details to `../recognition-workflows/`.
4. If no face is detected but the downstream process can tolerate full-image fallback, set `enforce_detection=False` and record the limitation.
