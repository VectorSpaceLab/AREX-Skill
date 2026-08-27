# Model Inference API Reference

This reference summarizes the TIAToolbox inference surfaces most agents need when planning or reviewing model runs. Treat it as a contract checklist, not as a replacement for runtime validation.

## Engine Constructors

All listed engines accept the same constructor pattern:

```python
EngineClass(model, batch_size=8, num_workers=0, weights=None, device="cpu", verbose=True)
```

- `model` may be a TIAToolbox pretrained model key or a compatible `ModelABC`/PyTorch module object.
- `weights` may be a local weights path. If `model` is a pretrained model key and `weights=None`, TIAToolbox may download pretrained weights.
- `device` is passed through PyTorch device handling; use `"cpu"`, `"cuda"`, `"cuda:0"`, or `"mps"` only when available.
- `batch_size` controls forward-pass patch count; lower it for CPU, memory pressure, or large segmentation patches.
- `num_workers=0` is safest for portable plans and notebook/debug contexts.

| Engine | Primary use | Notes |
| --- | --- | --- |
| `PatchPredictor` | Patch classification or WSI patch classification | Supports patch and WSI modes; can return labels and probabilities. |
| `DeepFeatureExtractor` | Embedding extraction from patches or WSIs | Supports `dict` and `zarr`; not `AnnotationStore`. |
| `SemanticSegmentor` | Dense semantic segmentation | Supports `dict`, `zarr`, `qupath`, and `annotationstore` flows depending on mode. |
| `NucleusDetector` | Point/object nucleus detection | Adds `min_distance`, `threshold_abs`, `threshold_rel`, and post-processing tile controls. |
| `MultiTaskSegmentor` | HoVerNet/HoVerNetPlus-style multitask segmentation | Preferred for nucleus instance segmentation and multi-head outputs. |
| `NucleusInstanceSegmentor` | Legacy nucleus instance segmentation | Deprecated since 2.1.0; migrate plans to `MultiTaskSegmentor`. |

## Run Contract

The common run shape is:

```python
output = engine.run(
    images=inputs,
    masks=masks,
    patch_mode=True,
    save_dir=output_dir,
    output_type="dict",
    ioconfig=ioconfig,
    batch_size=8,
    num_workers=0,
    device="cpu",
    overwrite=False,
)
```

Important fields:

- `images`: list of image paths, `WSIReader` objects, or patch arrays. Patch arrays should already match the model's expected input size and channel convention.
- `masks`: optional mask paths or arrays for WSI mode. Mask generation and patch extraction fundamentals belong in `../image-preprocessing/`.
- `patch_mode=True`: inputs are ready patches or patch-like images. Use `False` for WSI/tile extraction workflows.
- `save_dir`: required when output is file-backed or when WSI mode needs per-slide outputs.
- `output_type`: common choices are `"dict"`, `"zarr"`, `"annotationstore"`, and `"qupath"`; support differs by engine.
- `input_resolutions`, `output_resolutions`, `patch_input_shape`, `patch_output_shape`, and `stride_shape`: used when not relying on a pretrained model's bundled IO config.
- `memory_threshold`: percentage threshold for caching/tile behavior; lower it to force safer tiled processing.
- `output_file`: optional explicit output filename such as `"predictions.zarr"` or `"detections.db"`.
- `auto_get_mask`: WSI workflows may generate a tissue mask when masks are absent; explicit masks are safer when reproducibility matters.

## IO Config Classes

Use `IOPatchPredictorConfig` for patch classification and feature extraction; use `IOSegmentorConfig` for semantic, detection, and multitask segmentation.

```python
from tiatoolbox.models.engine.io_config import IOPatchPredictorConfig, IOSegmentorConfig

patch_ioconfig = IOPatchPredictorConfig(
    input_resolutions=[{"units": "mpp", "resolution": 0.5}],
    patch_input_shape=(224, 224),
    stride_shape=(224, 224),
    output_resolutions=[{"units": "mpp", "resolution": 0.5}],
)

segment_ioconfig = IOSegmentorConfig(
    input_resolutions=[{"units": "mpp", "resolution": 0.5}],
    output_resolutions=[{"units": "mpp", "resolution": 0.5}],
    patch_input_shape=(256, 256),
    patch_output_shape=(256, 256),
    stride_shape=(256, 256),
    save_resolution={"units": "mpp", "resolution": 0.5},
)
```

Validation rules:

- Resolution dictionaries use keys `"units"` and `"resolution"`.
- Supported resolution units are `"baseline"`, `"mpp"`, and `"power"` for model IO configs.
- Do not mix units across `input_resolutions`, `output_resolutions`, and `save_resolution` in one config.
- `stride_shape` defaults to `patch_input_shape` when omitted, but explicit stride is better for WSI plans.
- Segmentation `patch_output_shape` should reflect the model output crop/shape, not blindly copy input shape unless verified.
- For pretrained model keys, prefer the registry-provided `ioconfig` unless using a custom architecture or custom weights.

## Output Types

| Output type | Use when | Validation |
| --- | --- | --- |
| `dict` | Fast patch-mode smoke tests or in-memory downstream logic | Check keys such as `predictions`, `probabilities`, labels, task outputs, or coordinates as appropriate. |
| `zarr` | Large WSI outputs or feature tensors | Check the returned path exists, opens as Zarr, and contains expected arrays/chunks. |
| `annotationstore` | Spatial objects/classes for TIAToolbox annotation workflows | Check a `.db` path or `AnnotationStore` object is produced; visualize in `../annotation-visualization/`. |
| `qupath` | Interop with QuPath JSON workflows | Check generated `.json` files and coordinate scale. |

`DeepFeatureExtractor` supports only `dict` and `zarr`. Do not plan `annotationstore` for embeddings.

## CLI Planning Surface

The model CLIs mirror the API fields. Prefer the API for programmable workflows and the CLI for one-off batch plans.

| CLI command | Default model | Default output type | Extra fields |
| --- | --- | --- | --- |
| `patch-predictor` | `resnet18-kather100k` | `AnnotationStore` | `--class-dict`, `--return-probabilities` |
| `deep-feature-extractor` | `resnet18` | `zarr` | Embedding output; avoid `AnnotationStore` |
| `semantic-segmentor` | `fcn-tissue_mask` | `AnnotationStore` | `--output-resolutions`, `--patch-output-shape` |
| `nucleus-detector` | `mapde-conic` | `AnnotationStore` | `--min_distance`, `--threshold_abs`, `--threshold_rel`, `--postproc_tile_shape` |
| `nucleus-instance-segment` | `hovernet_fast-pannuke` | `AnnotationStore` | Deprecated route; prefer `multitask-segmentor` |
| `multitask-segmentor` | `hovernetplus-oed` | `AnnotationStore` | `--return-predictions` for task-array retention |

CLI JSON fields must be shell-quoted valid JSON, for example:

```bash
tiatoolbox semantic-segmentor \
  --input-resolutions '[{"units":"mpp","resolution":0.5}]' \
  --output-resolutions '[{"units":"mpp","resolution":0.5}]'
```

## Plan Validation Checklist

- Confirm engine matches task: classification, embeddings, semantic classes, detection points, or multitask instances.
- Confirm `model` key exists or the plan supplies a compatible custom model object and local weights.
- Confirm no-download mode uses a local `weights` path or a custom in-memory model, not a pretrained key with `weights=None`.
- Confirm device availability before using `cuda` or `mps`.
- Confirm IO config resolution units, patch shapes, output shapes, stride, and output resolution are consistent.
- Confirm output type is supported by the chosen engine and downstream consumer.
- Confirm WSI mode has masks or a documented `auto_get_mask` choice and has a `save_dir`.
