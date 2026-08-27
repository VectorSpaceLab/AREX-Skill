# Classification troubleshooting

## Import fails before a classifier is selected

**Symptom:** importing `PytorchWildlife` or its classification namespace fails
inside an unrelated legacy detection dependency.

**Action:** confirm the installed distribution is 1.3.0 and Python is >=3.10;
run the import in the supported modern package environment; then capture the
first exception and dependency versions. The root package eagerly imports many
model families, so a legacy `yolov5` compatibility problem can block a
classification import. Repair the package/environment compatibility using the
current supported dependency set, without copying a private compatibility shim
into application code. Do not claim the classifier is broken until a direct
namespace import succeeds.

## Constructor attempts an unwanted download

**Symptom:** `pretrained=True` or a TIMM wrapper with no local `weights` starts
network activity or fails with a URL/cache error.

**Action:** use `pretrained=False` plus a local `weights` path for Amazon,
Opossum, or Serengeti; provide a local path for Deepfaune or DFNE. Check the
path is readable before constructing the object. No package classifier can
infer from an absent checkpoint. Never solve a network failure by silently
switching to a different model or version.

## Amazon version is rejected or behaves unexpectedly

Use only `version="v1"` or `version="v2"` with `AI4GAmazonRainforest`; the
constructor default is `v2`. The package has 36 output classes for either
version. An unsupported version is not a documented fallback and can produce
an initialization error rather than a helpful validation message.

## Custom checkpoint key or architecture mismatch

**Symptoms:** `KeyError: state_dict`, missing/unexpected keys, or a size
mismatch for `classifier.weight`.

**Action:** run the bundled read-only helper:

```bash
python scripts/inspect_classifier_checkpoint.py <checkpoint>
```

For `CustomWeights`, require a `state_dict` entry and a PlainResNet-50
checkpoint compatible with the full inference module. The number of output
rows in the classifier head must equal `len(class_names)`. Supply a contiguous
zero-based list or integer-keyed map. Names are metadata and cannot repair a
checkpoint whose head has the wrong number of outputs.

TIMM checkpoints use different keys: Deepfaune expects `state_dict` and strips
`base_model.`; DFNE expects `model_state_dict` and strips no prefix. Do not
rename keys blindly. Compare the helper's prefix summary with the wrapper's
expected key before editing a checkpoint.

The diagnostic uses PyTorch's restricted `weights_only` loader and does not
construct a model. Do not add an unsafe fallback loader for an untrusted file.

## `class_names` failure

`CustomWeights(class_names=None)` fails because the implementation immediately
computes its length. A mapping must support every integer index from `0` to
`N-1`; a list/tuple must have exactly `N` entries. `DeepfauneClassifier` accepts
only `class_name_lang="fr"`, `"en"`, `"it"`, or `"de"`; an unsupported language
is a key error, not an automatic English fallback.

## Image conversion or transform errors

Use an RGB path or HWC RGB array. Normalize grayscale, RGBA, CHW, floating
range, and object arrays before calling a single-image method. PlainResNet's
path branch does not explicitly call `.convert("RGB")`, while the TIMM path
branch does; explicit RGB conversion is therefore the portable choice. The
default transform resizes to 224 for PlainResNet and 182 for TIMM and applies
ImageNet normalization.

## Batch returns no rows or crashes during concatenation

Check that the directory exists, contains at least one recognized extension,
and is not empty. `ClassificationImageFolder` searches recursively but does
not use folder names as labels. For crop batches, check that detector results
contain a `supervision.Detections` object with `.xyxy` and `.class_id`, that
source `img_id` paths resolve under the chosen crop root, and that at least one
row has the configured animal class id (default 0).

## Detector and classifier results are misaligned

`DetectionCrops` drops every non-animal detection and returns no detection
index or box. A counter that advances over every detection will attach the
wrong species to non-animal rows. Recreate the exact filter/order in a sidecar
list and assert its length equals the classifier result list. Preserve
`img_id`, detection index, and `xyxy` in that sidecar. If `path_head` changes
relative paths, do not use the post-join crop path as the only source identity.

## Identifier stripping changes more than expected

`id_strip` is passed to `str.strip`, which removes any of the specified
characters at both ends. It is not `removeprefix` and is not a path join
operation. Pass `None` for untouched ids and normalize roots explicitly when
merging detector and classifier records.

## Result fields look incomplete or repeated

Opossum intentionally emits no `all_confidences`; its single-logit confidence
is the selected binary class probability. Other current multiclass wrappers
build `all_confidences` from the first batch row, so a batch can contain
repeated distributions. Use `class_id` and `confidence` for batch decisions,
or create a tested per-row adapter from logits before serialization. Route
schema conversion to data-and-postprocessing.

## Device or memory error

Start with `device="cpu"`, `batch_size=1` (TIMM), and `num_workers=0`. For
CUDA, verify `torch.cuda.is_available()` and move the selected device and model
consistently. The 182-pixel DINOv2 model and PlainResNet-50 can use substantial
memory; reduce batch size before changing image semantics. A CPU API smoke
check does not prove CUDA forward performance.
