# Classification pipelines

These recipes describe package-level calls without requiring a checkout, demo
assets, a service, or an automatic weight download. Replace local placeholders
with user-owned files and use a cached or explicitly downloaded checkpoint.

## Single image

```python
import numpy as np
from PIL import Image
from PytorchWildlife.models import classification as pw_classification

classifier = pw_classification.AI4GAmazonRainforest(
    weights="<local-amazon-checkpoint>", device="cpu", pretrained=False, version="v2"
)
img = np.asarray(Image.open("<rgb-image>").convert("RGB"))
result = classifier.single_image_classification(
    img, img_id="images/example.jpg"
)
# result is one dict: inspect result["prediction"], result["class_id"],
# and result["confidence"] before consuming it.
```

A path string can be passed directly to TIMM classifiers. For portable behavior
across PlainResNet and TIMM wrappers, normalize a path to an RGB HWC array as
above. A custom `img_id` is recommended; otherwise the wrapper stringifies
`None`.

## Batch folder classification

```python
from PytorchWildlife.models import classification as pw_classification

classifier = pw_classification.DFNE(
    weights="<local-dfne-checkpoint>", device="cpu"
)
results = classifier.batch_image_classification(
    data_path="<image-folder>", batch_size=8, num_workers=0, id_strip=None
)
# results is ordered like the dataset traversal and contains one dict per image.
```

`AI4GAmazonRainforest`, `AI4GOpossum`, `AI4GSnapshotSerengeti`, and
`CustomWeights` accept the shorter batch signature and internally use batch
size 32 with four workers. TIMM wrappers expose batch size and worker count.
For a tiny fixture or notebook, use `num_workers=0` where available.

The source scans recursively and recognizes `.jpg`, `.jpeg`, `.png`, `.ppm`,
`.bmp`, `.pgm`, `.tif`, `.tiff`, and `.webp`. It does not infer labels from
subdirectory names: this is inference-only folder loading.

## Single detector crop

For a single detector result, preserve the detector image identifier and
index before cropping. The classifier does not know the detector's bbox or
index unless the caller supplies that metadata:

```python
import numpy as np
from PIL import Image
import supervision as sv
from PytorchWildlife.models import classification as pw_classification

classifier = pw_classification.AI4GOpossum(
    weights="<local-opossum-checkpoint>", device="cpu", pretrained=False
)
source_id = "images/camera-01/frame-0007.jpg"
input_img = np.asarray(Image.open(source_id).convert("RGB"))
xyxy = np.asarray([100, 80, 420, 360])  # one detector box in xyxy pixels
crop = sv.crop_image(input_img, xyxy=xyxy)
classification = classifier.single_image_classification(
    crop, img_id=source_id
)
combined = {
    "source_img_id": source_id,
    "detection_index": 0,
    "xyxy": xyxy.tolist(),
    "classification": classification,
}
```

Use the detector's animal class id, not a classifier class id, when deciding
which boxes to crop. Detection configuration and detector result creation
belong to `../detection/SKILL.md`.

## Batch detector crops

A detector batch result must be an iterable of dictionaries like:

```text
[
  {
    "img_id": "images/frame-a.jpg",
    "detections": supervision.Detections(...),
    "labels": [...],
    ...
  },
  ...
]
```

The `detections` object must provide `xyxy` and `class_id`. Pass the complete
result list to the classifier; it creates `DetectionCrops` internally:

```python
classifier = pw_classification.AI4GAmazonRainforest(
    weights="<local-amazon-checkpoint>", device="cpu", pretrained=False
)
clf_results = classifier.batch_image_classification(
    det_results=det_results, id_strip=None
)
```

`DetectionCrops` flattens only rows with `class_id == 0` by default, in source
image order and then box order. It returns a path for each crop, but not the
box index. Build a sidecar list with the identical filter before the call:

```python
sidecar = []
for det in det_results:
    for detection_index, (xyxy, class_id) in enumerate(
        zip(det["detections"].xyxy, det["detections"].class_id)
    ):
        if int(class_id) == 0:
            sidecar.append({
                "img_id": det["img_id"],
                "detection_index": detection_index,
                "xyxy": np.asarray(xyxy).tolist(),
            })
assert len(sidecar) == len(clf_results)
for meta, result in zip(sidecar, clf_results):
    result["source_img_id"] = meta["img_id"]
    result["detection_index"] = meta["detection_index"]
    result["xyxy"] = meta["xyxy"]
```

If a non-default animal class is used, construct `DetectionCrops` yourself
with `animal_cls_id=<detector-animal-class-id>` and feed a compatible loader
through a dedicated adapter; the public wrapper's `batch_image_classification`
only accepts `data_path` or `det_results` and always uses its default crop
settings.

## Merging labels safely

Do not increment a classifier-result counter for every detector row. Increment
only when the detector class passes the same animal filter used by
`DetectionCrops`; non-animal detections have no classifier result. Prefer
attaching classification metadata to each sidecar row and then handing the
merged detector object to the post-processing workflow. Classification itself
should return raw result dictionaries; JSON, timelapse, annotated images, and
video are owned by `../data-and-postprocessing/SKILL.md`.

## Custom checkpoint workflow

1. Run [the checkpoint diagnostic](../scripts/inspect_classifier_checkpoint.py)
   with a local path. It performs no model construction or download.
2. Confirm a `state_dict` entry and a PlainResNet classifier output dimension.
3. Create a contiguous class map/list with exactly that many names.
4. Construct `CustomWeights(weights=..., class_names=..., device=...)`.
5. Run one RGB tiny fixture before a directory or crop batch.

An illustrative custom-weight workflow uses a dictionary keyed by integer
class ids and a detector-crop workflow, but its legacy call passes a
`DataLoader` to `batch_image_classification`; that does not match the 1.3.0
public signature. Use `det_results=` or `data_path=` instead, and treat that
workflow as conceptual rather than an executable dependency.
