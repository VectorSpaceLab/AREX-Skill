# Detection API reference

## Constructors

These are the inspected public signatures. `self` is omitted in the table.
Defaults are part of the runtime contract.

| Class | Signature |
|---|---|
| `MegaDetectorV5` | `(weights=None, device='cpu', pretrained=True, version='a')` |
| `MegaDetectorV6` | `(weights=None, device='cpu', pretrained=True, version='MDV6-yolov9-c')` |
| `MegaDetectorV6MIT` | `(weights=None, device='cpu', pretrained=True, version='MDV6-mit-yolov9-c')` |
| `MegaDetectorV6Apache` | `(weights=None, device='cpu', pretrained=True, version='MDV6-apa-rtdetr-c')` |
| `HerdNet` | `(weights=None, device='cpu', version='general', url=<default>, transform=None)` |
| `OWLC` | `(weights=None, device='cpu', version='general', url=<default>, transform=None)` |
| `OWLT` | `(weights=None, device='cpu', url=<default>, transform=None)` |
| `DeepfauneDetector` | `(weights=None, device='cpu')` |
| `MegaDetectorV6_Distributed` | `(weights=None, device='cpu', pretrained=True, version='MDV6-yolov9-c')` |

The `url=<default>` values are intentionally not reproduced here. They are
network side effects, not stable application inputs. Supply `weights` for a
known local checkpoint or arrange the package cache before inference.

## Inference methods

The standard single-image methods are:

- Ultralytics-backed (`MegaDetectorV5`, standard `MegaDetectorV6`,
  `DeepfauneDetector`):
  `single_image_detection(img, img_path=None, det_conf_thres=0.2, id_strip=None)`.
- MIT and Apache V6: the same argument names and defaults, without a return
  annotation in the inspected source.
- `HerdNet`:
  `single_image_detection(img, img_path=None, det_conf_thres=0.2,
  clf_conf_thres=0.2, id_strip=None)`.
- `OWLC` and `OWLT`:
  `single_image_detection(img, img_path=None, det_conf_thres=0.20,
  id_strip=None)`.

For normal folder inference, the standard methods are:

- `MegaDetectorV5`: `batch_image_detection(data_path, batch_size=16,
  det_conf_thres=0.2, id_strip=None)`.
- standard `MegaDetectorV6` and `DeepfauneDetector`:
  `batch_image_detection(data_source, batch_size=16, det_conf_thres=0.2,
  id_strip=None)`. The source accepts a directory or a list/array sequence of
  HWC arrays.
- MIT and Apache V6: `batch_image_detection(data_path, batch_size=16,
  det_conf_thres=0.2, id_strip=None)`.
- `HerdNet`: `batch_image_detection(data_path, det_conf_thres=0.2,
  clf_conf_thres=0.2, batch_size=1, id_strip=None)`.
- `OWLC` and `OWLT`: `batch_image_detection(data_path, det_conf_thres=0.20,
  batch_size=1, id_strip=None)`.

The distributed class instead requires
`batch_image_detection(loader, batch_size, global_rank, local_rank, output_dir,
det_conf_thres=0.2, checkpoint_frequency=1000)` and has a different output
schema. It is not interchangeable with the standard methods.

## Inputs and identifiers

- A path-like string passed to `img` is opened and converted to RGB. Set
  `img_path` when an ndarray needs a meaningful identifier; otherwise some
  wrappers produce `img_id=None` or return the ndarray under `img`.
- A direct ndarray should be an RGB HWC array. Use a Python list of such arrays
  for the standard V6/Deepfaune array-batch path. A single HWC ndarray is not
  an image sequence for that method; its first dimension would be interpreted
  as the sequence length.
- Directory batches use recursive image discovery for the common JPG, JPEG,
  PNG, PPM, BMP, PGM, TIFF, and WEBP extensions. The underlying directory walk
  does not promise a sorted order, so retain returned `img_id` values.
- `id_strip` is passed to `str(...).strip(id_strip)`. It removes any matching
  characters from both ends; it is not a prefix or directory-base operation.

## Output schema and coordinates

Normal wrappers return a dictionary with:

```text
img_id: string-like identifier, when the wrapper has one
detections: supervision.Detections
labels: list[str]
normalized_coords: optional list[list[float]]
```

`detections.xyxy` is an `N x 4` NumPy-like array in pixel coordinates in
`[x1, y1, x2, y2]` order. `detections.confidence` and `class_id` align row by
row. An empty prediction is represented as an empty detections object; do not
assume there is at least one row. Labels are formatted from `CLASS_NAMES` and
confidence. Use `model.CLASS_NAMES` as the authoritative class map.

`normalized_coords` is emitted by standard V5/V6/Deepfaune single and batch
paths, and by HerdNet/OWL/Apache/MIT folder-batch paths. It is not consistently
emitted by HerdNet/OWL/Apache/MIT single-image paths. The intended formula is
`[x1/W, y1/H, x2/W, y2/H]`, but several localization/Apache batch paths divide
using source size indices that are transposed relative to their `(H, W)` or
`(W, H)` representation. When normalized coordinates affect filtering,
Timelapse data, or evaluation, recompute them from the original image width
and height using `detections.xyxy`.

## Threshold and weight semantics

`det_conf_thres` is forwarded to the detector's confidence filtering; defaults
are `0.2` (or `0.20`, numerically the same). HerdNet also requires
`clf_conf_thres`; a candidate survives only when both classification and
 detection scores are strictly greater than their thresholds. OWL uses only a
detection score.

`weights` behavior is wrapper-specific:

- V5 loads a local checkpoint when supplied; otherwise `pretrained=True` selects
  a remote URL. With `pretrained=False` and no local weights, construction fails
  with `Need weights for inference.`
- Standard V6 and Deepfaune prefer a supplied local weight in their underlying
  loader. Standard V6 nevertheless assigns its remote URL regardless of the
  `pretrained` flag, so `pretrained=False` alone is not an offline switch.
- HerdNet, OWLC, and OWLT load a supplied local checkpoint and otherwise use
  their URL/cache path. Their checkpoints carry normalization metadata; custom
  files must match the expected checkpoint structure.
- Apache V6 prefers a supplied local checkpoint, but its accepted `pretrained`
  flag does not disable the configured URL by itself. MIT V6's base
  implementation reconstructs its configuration and uses its configured
  URL/cache when inference starts; the passed `weights` value is not honored as
  a general offline override. Treat MIT custom-weight inference as unsupported
  unless the exact installed implementation has been tested.

Never call a default pretrained constructor merely to inspect its signature.
Use the linked environment checker for read-only diagnostics.
