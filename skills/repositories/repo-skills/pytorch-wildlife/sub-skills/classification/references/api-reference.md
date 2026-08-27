# Classification API reference

Import the public namespace as:

```python
from PytorchWildlife.models import classification as pw_classification
from PytorchWildlife.data import datasets as pw_data
from PytorchWildlife.data import transforms as pw_trans
```

## Constructors

```text
AI4GAmazonRainforest(weights=None, device="cpu", pretrained=True, version="v2")
AI4GOpossum(weights=None, device="cpu", pretrained=True)
AI4GSnapshotSerengeti(weights=None, device="cpu", pretrained=True)
DeepfauneClassifier(weights=None, device="cpu", transform=None, class_name_lang="en")
DFNE(weights=None, device="cpu", transform=None)
CustomWeights(weights=None, class_names=None, device="cpu")
```

All concrete constructors create and load weights immediately. The
`BaseClassifierInference` and bare base classes are implementation shells, not
ready-to-use classifiers. A pretrained/default URL is network-active if the
required file is not already cached. A local `weights` path takes precedence
over the URL in the PlainResNet wrappers and is used instead of the URL in the
TIMM wrapper.

| Wrapper | Backbone setup | Local checkpoint lookup |
|---|---|---|
| Amazon, Opossum, Serengeti, CustomWeights | `PlainResNetClassifier`; 18 or 50 layers as listed in the model overview | `checkpoint["state_dict"]`, loaded strictly into the full inference module |
| DeepfauneClassifier | TIMM `vit_large_patch14_dinov2.lvd142m`, `num_classes=34` | `checkpoint["state_dict"]`, remove `base_model.` from each key |
| DFNE | Same TIMM backbone, `num_classes=24` | `checkpoint["model_state_dict"]`, no prefix removal |

`CustomWeights` sets `num_cls = len(class_names)` and always builds the
PlainResNet-50 head. Although its annotation says `list[str]`, the implementation
also works with an integer-keyed mapping such as `{0: "animal-a", 1: "animal-b"}`.
The keys must be exactly the contiguous class ids used by the checkpoint.

## Preprocessing

`Classification_Inference_Transform(target_size=224, **kwargs)` composes:

1. `Resize((target_size, target_size), **kwargs)`;
2. `ToTensor()`;
3. normalization with mean `[0.485, 0.456, 0.406]` and standard deviation
   `[0.229, 0.224, 0.225]`.

PlainResNet wrappers use target size 224. TIMM wrappers use target size 182;
Deepfaune overrides interpolation to bicubic and passes `max_size=None` and
`antialias=None`. A custom transform replaces the wrapper's default transform.

Single-image methods accept `img` as a path string or an HWC array convertible
by `PIL.Image.fromarray`; pass `img_id` separately if the output identifier
must not be `"None"`. Use RGB data. The method is:

```text
single_image_classification(img, img_id=None, id_strip=None) -> dict
```

`id_strip` is passed to `str(img_id).strip(id_strip)`. It removes any matching
characters at either end; it does not remove an arbitrary directory prefix.
Use a pre-normalized identifier or perform explicit prefix handling outside
this API when exact path identity matters.

## Batch methods

PlainResNet wrappers expose:

```text
batch_image_classification(data_path=None, det_results=None, id_strip=None) -> list[dict]
```

TIMM wrappers additionally expose:

```text
batch_image_classification(
    data_path=None, det_results=None, id_strip=None,
    batch_size=32, num_workers=0, **kwargs
) -> list[dict]
```

Pass exactly one of `data_path` and `det_results`. `data_path` is recursively
searched by `ClassificationImageFolder`; the dataset includes extensions
`.jpg`, `.jpeg`, `.png`, `.ppm`, `.bmp`, `.pgm`, `.tif`, `.tiff`, and `.webp`.
Each item is `(transformed_tensor, image_path)`, and output order follows the
DataLoader's non-shuffled dataset order. An empty directory is not a valid
batch: concatenation has no logits and fails.

PlainResNet uses a fixed batch size of 32 and four workers. TIMM defaults to
32 and zero workers and forwards extra DataLoader keyword arguments. Reduce
workers for notebooks, Windows, tiny fixtures, or debugging.

## Result dictionaries

For Amazon, Serengeti, CustomWeights, Deepfaune, and DFNE, each result has:

| Field | Type | Meaning |
|---|---|---|
| `img_id` | `str` | Input path or supplied identifier after `id_strip` |
| `prediction` | `str` | Label for the argmax class |
| `class_id` | `int` | Zero-based argmax class id |
| `confidence` | `float` | Maximum softmax probability |
| `all_confidences` | `list[list[str, float]]` | Class label/probability pairs |

The implementation obtains `all_confidences` from the first row of the logits.
For a single image it is the expected distribution. For a multi-image batch,
the same first-image distribution is currently repeated in every result. Do
not treat it as per-image calibrated evidence; retain `class_id` and
`confidence`, or compute a per-row distribution from raw logits in a separate
validated adapter.

`AI4GOpossum` is different: it applies sigmoid to one logit, predicts class 1
when probability is greater than 0.5 and class 0 otherwise, and emits
`img_id`, `prediction`, `class_id`, and `confidence` only. Its confidence is
`p` for Opossum and `1-p` for Non-opossum. It does **not** emit
`all_confidences`; add an explicit binary schema adapter before sending it to a
serializer that requires that field.

## Dataset contracts

```text
ClassificationImageFolder(image_dir, transform=None)
DetectionCrops(detection_results, transform=None, path_head=None, animal_cls_id=0)
```

`DetectionCrops` expects an iterable of detector result dictionaries. Each
entry must contain `img_id` and a `supervision.Detections` object under
`detections`; the object must expose `.xyxy` and `.class_id`. It records only
rows where `class_id == animal_cls_id`, in input order, and loads each source
image as RGB before cropping. If `path_head` is set, the crop loader joins it
to `img_id`; the classifier wrappers call it with `path_head="."`.

The dataset returns only `(crop_tensor, crop_path)`. It does not return the
source detection index, bounding box, confidence, or detector result object.
If those fields matter, maintain a sidecar mapping in the same filtered loop
or use a dedicated adapter that carries `(img_id, detection_index, xyxy)` next
to each classifier result.
