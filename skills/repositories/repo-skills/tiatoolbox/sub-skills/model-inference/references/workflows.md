# Model Inference Workflows

Use these patterns to turn a user request into a safe TIAToolbox inference plan. Keep WSI reader setup, mask generation, and visualization in their sibling sub-skills when those topics dominate the task.

## CPU-Only Patch Prediction Without Downloads

Use this when the user has local weights or a custom model and no network/GPU assumptions are allowed.

```python
from tiatoolbox.models.engine.io_config import IOPatchPredictorConfig
from tiatoolbox.models.engine.patch_predictor import PatchPredictor

predictor = PatchPredictor(
    model=custom_model_or_registry_key,
    weights="local_weights.pth",
    batch_size=4,
    num_workers=0,
    device="cpu",
    verbose=True,
)

ioconfig = IOPatchPredictorConfig(
    input_resolutions=[{"units": "mpp", "resolution": 0.5}],
    output_resolutions=[{"units": "mpp", "resolution": 0.5}],
    patch_input_shape=(224, 224),
    stride_shape=(224, 224),
)

result = predictor.run(
    images=patch_paths,
    patch_mode=True,
    ioconfig=ioconfig,
    output_type="dict",
    return_probabilities=True,
)
```

Validate by checking that `result` is a dictionary with prediction records for every input patch and, when requested, probability vectors or class labels with expected lengths. If output is file-backed, check path existence and format-specific openability.

## WSI Classification or Feature Extraction

- Use `patch_mode=False` for WSIs and provide `save_dir`.
- Provide explicit `masks` when the mask is part of the scientific protocol; otherwise document `auto_get_mask=True`.
- Use `output_type="zarr"` for large WSI classification maps or embeddings.
- For embeddings, use `DeepFeatureExtractor` and avoid `annotationstore`.
- Start with `batch_size=1` or a small value on CPU, then increase only after a successful smoke run.

## Semantic Segmentation

```python
from tiatoolbox.models import IOSegmentorConfig, SemanticSegmentor

segmentor = SemanticSegmentor(model="fcn-tissue_mask", device="cpu", batch_size=8)
segment_ioconfig = IOSegmentorConfig(
    input_resolutions=[{"units": "mpp", "resolution": 0.5}],
    output_resolutions=[{"units": "mpp", "resolution": 0.5}],
    patch_input_shape=(256, 256),
    patch_output_shape=(256, 256),
    stride_shape=(256, 256),
    save_resolution={"units": "mpp", "resolution": 0.5},
)

output = segmentor.run(
    images=wsi_paths,
    masks=mask_paths,
    patch_mode=False,
    save_dir="semantic-output",
    output_type="annotationstore",
    ioconfig=segment_ioconfig,
    memory_threshold=80,
)
```

Validate by confirming the output path/object, class mapping, scale factor, and coordinate frame. Send visualization and store editing to `../annotation-visualization/`.

## Nucleus Detection

Use `NucleusDetector` for detection point workflows where the user wants nucleus centroids or object annotations rather than dense semantic masks.

Plan these fields explicitly:

- `model`: detection model key or custom detector.
- `output_type`: usually `annotationstore`, `qupath`, or `zarr` depending on downstream use.
- `min_distance`, `threshold_abs`, `threshold_rel`: only set when the user provides or validates a detection protocol.
- `postproc_tile_shape`: use for large-slide post-processing memory control.
- `memory_threshold`: lower values force more conservative tile/caching behavior.

## Migrating NucleusInstanceSegmentor Plans

`NucleusInstanceSegmentor` is deprecated since 2.1.0. Prefer `MultiTaskSegmentor` while preserving the user's model key, IO config, output format, and return-prediction intent.

Migration pattern:

```python
from tiatoolbox.models import IOSegmentorConfig, MultiTaskSegmentor

segmentor = MultiTaskSegmentor(
    model="hovernet_fast-pannuke",
    weights=local_weights_or_none,
    batch_size=8,
    num_workers=0,
    device="cpu",
)

output = segmentor.run(
    images=inputs,
    masks=masks,
    patch_mode=patch_mode,
    save_dir="instance-output",
    output_type="annotationstore",
    ioconfig=ioconfig,
    return_predictions=return_predictions,
    return_probabilities=True,
)
```

Preserve `output_type` exactly unless it is unsupported or inappropriate. If the old plan expected task arrays, carry forward `return_predictions`; if it only needed spatial objects, keep `annotationstore` or `qupath` and avoid returning large arrays.

## CLI Review Pattern

Before recommending a CLI command:

1. Verify the command name maps to the intended engine.
2. Validate the model key using `scripts/model_registry_probe.py` or state that the model is a custom object unavailable to CLI.
3. Check JSON options such as `--input-resolutions`, `--output-resolutions`, and `--class-dict` are valid JSON strings.
4. Check mode: `--patch-mode true` for patch files and `false` for WSI processing.
5. Check `--output-path` and `--output-type` are compatible with the engine.
6. Check `--weights` is present when network downloads are not allowed.

Example CLI skeleton for a no-download CPU plan:

```bash
tiatoolbox patch-predictor \
  --img-input patches/ \
  --output-path patch-prediction/ \
  --model resnet18-kather100k \
  --weights local_weights.pth \
  --device cpu \
  --batch-size 4 \
  --num-workers 0 \
  --patch-mode true \
  --output-type zarr \
  --overwrite false
```

## Output Validation Matrix

- `dict`: check Python type, per-input count, expected keys, class/probability shapes, and absence of unexpected dropped keys.
- `zarr`: open the Zarr group/array, inspect root keys, chunk shape, dtype, and spatial dimensions.
- `annotationstore`: open the store with TIAToolbox annotation APIs and count annotations/properties.
- `qupath`: parse JSON, check geometry coordinates and class labels.
- Multitask outputs: confirm each expected task is present or intentionally omitted by `return_predictions`.
