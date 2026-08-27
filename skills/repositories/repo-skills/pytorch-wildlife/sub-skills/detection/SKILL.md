---
name: detection
description: "Operate Pytorch-Wildlife image detectors for camera-trap and
  overhead wildlife localization, including MegaDetector V5/V6, HerdNet, OWL,
  public variants, local weights, batching, and result interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Detection

Use this skill when the request is to locate animals, people, or vehicles in
images with Pytorch-Wildlife 1.3.0. It covers camera-trap images, overhead
wildlife imagery, single-image inference, image-folder batches, local detector
weights, device choice, confidence thresholds, and the standard
`supervision.Detections` result contract.

Load the linked references for exact signatures, model/version tables, output
caveats, and recovery steps:

- [model overview](references/model-overview.md)
- [API reference](references/api-reference.md)
- [workflows](references/workflows.md)
- [troubleshooting](references/troubleshooting.md)
- [environment checker](scripts/check_detection_environment.py)

## Route the request

1. Decide whether the imagery is ordinary camera-trap imagery or overhead/aerial
   imagery. Start with MegaDetector V6 for ordinary wildlife detection. Use
   OWL-C or OWL-T for overhead imagery and HerdNet for dense-herd localization
   or counting-oriented workflows.
2. Select the wrapper and exact version before constructing it. V5 uses `a` or
   `b`; the standard V6 wrapper accepts only the five `MDV6-*` values documented
   in the API reference. MIT and Apache V6 variants are separate classes.
3. Decide whether weights may be fetched. For offline or custom-weight work,
   pass an existing local checkpoint with `weights=...` and use `device="cpu"`
   unless the checkpoint and CUDA stack have been verified.
4. Pick `single_image_detection` for one path or RGB HWC ndarray. Pick
   `batch_image_detection` for an image directory; only standard Ultralytics
   V6/Deepfaune wrappers also accept a sequence of RGB HWC ndarrays.
5. Inspect `result["detections"]` before post-processing. Route JSON, image
   annotation, crop/separation, and video output to `data-and-postprocessing`.
   Route detector-crop classification to `classification`, and training or
   fine-tuning to `fine-tuning`.

## Minimal public usage

```python
from PytorchWildlife.models import detection as pw_detection

model = pw_detection.MegaDetectorV6(
    device="cpu", weights="/path/to/local/model.pt",
    version="MDV6-yolov10-c",
)
one = model.single_image_detection("capture.jpg", det_conf_thres=0.20)
many = model.batch_image_detection("captures/", batch_size=16,
                                   det_conf_thres=0.20)
```

The path above is an input placeholder, not a required package location. Do
not construct a model with default pretrained settings in a no-network run.
The constructors can load weights during construction; the safe environment
checker never constructs a model.

## Quick selection checklist

- General camera-trap screening: standard `MegaDetectorV6`.
- Existing V5 workflow or checkpoint: `MegaDetectorV5`.
- Dense herds: `HerdNet`; overhead imagery: `OWLC` or `OWLT`.
- Licensing/backend-specific V6 needs: use the separate MIT or Apache wrapper.

## Result contract

For the normal detector wrappers, a result is a dictionary containing an image
identifier (`img_id`, or an image object for some ndarray calls), a
`supervision.Detections` object, and formatted `labels`. The detections object
contains `xyxy` (`N x 4` pixel boxes), `confidence` (`N`), and `class_id` (`N`).
MegaDetector classes map `0=animal`, `1=person`, and `2=vehicle`; always inspect
`model.CLASS_NAMES` for HerdNet, OWL, or third-party wrappers because their
class maps differ. `normalized_coords`, when supplied, is intended to contain
`[x1/W, y1/H, x2/W, y2/H]`; see the API reference before trusting it across
all wrappers.

## Operational guardrails

- Confidence thresholds default to `0.2` and are applied at inference. Validate
  caller-provided values in `[0, 1]`; the package does not provide a universal
  range check.
- HerdNet applies both `det_conf_thres` and `clf_conf_thres`, using strict
  greater-than comparisons. OWL has only a detection threshold.
- HerdNet, OWL-C, and OWL-T use patch/stitch inference and their source batch
  loops effectively process the first image of each loaded batch. Use
  `batch_size=1` for predictable operation.
- RGB arrays should be HWC (`height, width, 3`), not CHW. A directory batch
  recursively discovers common image extensions and preserves source paths.
- `id_strip` is passed to Python string `.strip`, so it removes matching
  characters at the ends rather than a path prefix.
- Default pretrained constructors may access the network and cache files.
  Missing cache files, optional legacy imports, and CUDA availability are
  operational prerequisites, not detection results.

For exact constructor signatures, supported versions, coordinate caveats,
custom-weight behavior, and specialized wrappers, use the references rather
than inferring from this router.
