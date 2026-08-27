# Image Loading and Visualization

Read this when converting image inputs between local paths, PIL, OpenCV/cv2 arrays, and NumPy arrays, or when plotting predictions in a notebook or headless environment.

## Image Loading Matrix

```python
from autodistill.helpers import load_image

load_image("image.jpg", return_format="PIL")    # Pillow Image
load_image("image.jpg", return_format="cv2")    # NumPy array in cv2/BGR style
load_image("image.jpg", return_format="numpy")  # NumPy array
```

`load_image` also accepts an existing Pillow `Image` or NumPy/cv2 array:

```python
pil_image = load_image(path, return_format="PIL")
cv2_image = load_image(pil_image, return_format="cv2")
round_trip = load_image(cv2_image, return_format="PIL")
```

Use the return format expected by the concrete plugin. The docs list common plugin expectations: Grounding DINO/Grounded SAM/FastSAM/SAM HQ often use cv2-like arrays, while CLIP/AltCLIP/MetaCLIP/VLPart/OWLViT-style plugins often use PIL-style inputs.

## URL Inputs

HTTP URLs are supported, but they fetch data with network calls. For deterministic checks, use local files or run `check_image_loading.py` without `--include-url`.

## Visualization with `plot`

```python
import cv2
from autodistill.utils import plot

image = cv2.imread("image.jpg")
annotated = plot(
    image=image,
    detections=detections,
    classes=base_model.ontology.classes(),
    raw=True,
)
```

Use `raw=True` when running in a headless environment or when you want to save the annotated array yourself. Use `raw=False` in notebooks or interactive sessions where `supervision.plot_image` can display the image.

## Comparing Models

```python
from autodistill.utils import compare

compare(models=[model_a, model_b], images=["image1.jpg", "image2.jpg"])
```

This calls every model on every image and plots a grid. Do not use it as an install check for heavyweight plugins; first run a single prediction per model and confirm downloads/GPU/credentials are approved.

## Safe Local Check

```bash
python scripts/check_image_loading.py
```

The script creates a tiny local fixture and verifies PIL/cv2/numpy/path conversion branches. Add `--include-url URL` only when network use is approved.
