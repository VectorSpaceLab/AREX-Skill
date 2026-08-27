# MultiModalPredictor API Reference

## Import

```python
from autogluon.multimodal import MultiModalPredictor
```

`MultiModalPredictor` supports text, image, tabular features inside a multimodal DataFrame, document inputs, NER, semantic matching, object detection, semantic segmentation, feature extraction, and zero-shot image/image-text tasks.

## Constructor

Verified signature:

```python
MultiModalPredictor(
    label=None,
    problem_type=None,
    query=None,
    response=None,
    match_label=None,
    presets=None,
    eval_metric=None,
    hyperparameters=None,
    path=None,
    verbosity=2,
    num_classes=None,
    classes=None,
    warn_if_exist=True,
    enable_progress_bar=None,
    pretrained=True,
    validation_metric=None,
    sample_data_path=None,
    use_ensemble=False,
    ensemble_size=2,
    ensemble_mode="one_shot",
)
```

Important constructor choices:

- `label`: target column for classification, regression, NER annotations, object detection RoIs, or segmentation masks.
- `problem_type`: use explicit values for non-standard tasks; omit only when standard classification/regression can be inferred from labels.
- `query`, `response`, `match_label`: required shape hints for trained semantic matching pairs.
- `presets`: quality preset such as `medium_quality`, `high_quality`, `best_quality`, or HPO variants when available.
- `hyperparameters`: override config keys, either as a dict, string, or list of key assignments.
- `path`: predictor artifact directory; specify it for reproducible training runs.
- `num_classes`, `classes`, `sample_data_path`: object detection and segmentation class discovery controls.
- `pretrained=False`: avoids pretrained initialization only when random initialization is intended; it can reduce network dependency but usually hurts quality.
- `use_ensemble=True`: only for multimodal classification/regression ensembles, not for every advanced problem type.

## Supported Problem Types

| Problem type | Typical data | Fit support | Zero-shot/inference without fit |
| --- | --- | --- | --- |
| `classification`, `binary`, `multiclass` | text/image/tabular/document features with categorical label | yes | no |
| `regression` | text/image/tabular/document features with numeric label | yes | no |
| `ner`, `named_entity_recognition` | text spans plus NER annotation label | yes | no |
| `text_similarity` | query and response text | yes | yes |
| `image_similarity` | query and response image paths/arrays | yes | yes |
| `image_text_similarity` | text-image or image-text pairs | yes | yes |
| `object_detection` | image paths plus COCO/VOC/DataFrame boxes | yes | yes |
| `semantic_segmentation` | image paths plus mask paths for fitting/eval | yes | yes |
| `feature_extraction` | text or image inputs | no | yes |
| `zero_shot_image_classification` | image inputs and candidate classes | no | yes |
| `few_shot_classification` | small text or image labeled data | yes | no |

`classification` is a generic classification request; AutoGluon resolves it to `binary` or `multiclass` after seeing labels. Unsupported `problem_type` values fail early with the registered problem type list.

## Core Methods

### `fit`

Verified signature:

```python
predictor.fit(
    train_data,
    presets=None,
    tuning_data=None,
    max_num_tuning_data=None,
    id_mappings=None,
    time_limit=None,
    save_path=None,
    hyperparameters=None,
    column_types=None,
    holdout_frac=None,
    teacher_predictor=None,
    seed=0,
    standalone=True,
    hyperparameter_tune_kwargs=None,
    clean_ckpts=True,
    predictions=None,
    labels=None,
    predictors=None,
)
```

Use `fit` for supervised multimodal tasks. `train_data` is usually a pandas DataFrame; for object detection it may also be a COCO/VOC annotation path. `column_types` pins inference when automatic type detection is ambiguous. `id_mappings` maps identifiers to text/image content in semantic search workflows where the pair table stores IDs rather than raw content.

### `predict`

Verified signature:

```python
predictor.predict(
    data,
    candidate_data=None,
    id_mappings=None,
    as_pandas=None,
    realtime=False,
    save_results=None,
    **kwargs,
)
```

`data` can be a DataFrame, dict, list, single image path, or annotation path depending on problem type. `candidate_data` is for matching/retrieval candidates. Object detection supports extra kwargs such as COCO-style result control; `save_results=True` is detection-focused.

### `predict_proba`

Verified signature:

```python
predictor.predict_proba(
    data,
    candidate_data=None,
    id_mappings=None,
    as_pandas=None,
    as_multiclass=True,
    realtime=False,
)
```

Use for classification probabilities and matching scores when supported. For binary tasks, `as_multiclass=True` returns probabilities for both classes.

### `evaluate`

Verified signature:

```python
predictor.evaluate(
    data,
    query_data=None,
    response_data=None,
    id_mappings=None,
    metrics=None,
    chunk_size=1024,
    similarity_type="cosine",
    cutoffs=[1, 5, 10],
    label=None,
    return_pred=False,
    realtime=False,
    eval_tool=None,
    predictions=None,
    labels=None,
)
```

Use `metrics` to request task-specific metrics. Matching/ranking evaluation can pass separate `query_data` and `response_data`; `chunk_size`, `similarity_type`, and `cutoffs` matter for retrieval. Object detection can use `eval_tool="pycocotools"` or `"torchmetrics"` when those dependencies are installed.

### `extract_embedding`

```python
predictor.extract_embedding(
    data,
    id_mappings=None,
    return_masks=False,
    as_tensor=False,
    as_pandas=False,
    realtime=False,
    signature=None,
)
```

Use for feature extraction, document/image/text embeddings, and custom retrieval. For matchers, `signature` can identify query or response side processing.

### Persistence and Summary

```python
predictor.save(path, standalone=True)
loaded = MultiModalPredictor.load(path, resume=False, verbosity=3)
summary = predictor.fit_summary(verbosity=0, show_plot=False)
```

`standalone=True` attempts to package downloaded model assets for offline use. `load` uses pickle-backed artifacts; only load trusted predictor directories.

### Deployment Methods

```python
onnx_path_or_bytes = predictor.export_onnx(data, path=None, batch_size=None, verbose=False, opset_version=16)
predictor.optimize_for_inference(providers=None)
```

See `deployment.md` before using these: ONNX export traces representative data and requires compatible optional runtime packages.

## Metrics

Common metric defaults and supported families:

- Binary: `roc_auc` fallback, also common classification metrics such as `accuracy`, `f1`, `average_precision`, and `log_loss` when available.
- Multiclass: `accuracy` fallback plus multiclass metrics.
- Regression: `root_mean_squared_error` / `rmse`, `r2`, `pearsonr`, `spearmanr`.
- Object detection: `map`, `mean_average_precision`, `map_50`, `map_75`, size-specific mAP/mAR variants.
- Semantic segmentation: `iou`, `ber`, `sm`.
- NER: `overall_f1`, `ner_token_f1`.
- Matching/retrieval: `recall`, `ndcg`, `precision`, `mrr` for ranking-style evaluation; similarity scoring often uses cosine.

## Hyperparameters and Config Keys

Top-level config groups include `model`, `data`, `optim`, `env`, `distiller`, and `matcher`.

Common overrides:

```python
hyperparameters = {
    "model.names": ["hf_text", "timm_image", "fusion_mlp"],
    "model.hf_text.checkpoint_name": "google/electra-small-discriminator",
    "model.timm_image.checkpoint_name": "swin_tiny_patch4_window7_224",
    "model.clip.checkpoint_name": "openai/clip-vit-base-patch32",
    "model.document_transformer.checkpoint_name": "microsoft/layoutlmv3-base",
    "model.mmdet_image.checkpoint_name": "yolov3_mobilenetv2_8xb24-320-300e_coco",
    "model.mmdet_image.output_bbox_format": "xyxy",
    "model.sam.checkpoint_name": "facebook/sam-vit-base",
    "optim.max_epochs": 1,
    "optim.lr": 1e-4,
    "optim.peft": "lora",
    "env.num_gpus": 0,
    "env.num_workers": 0,
    "env.num_workers_inference": 0,
    "env.precision": 32,
}
```

CPU-safe examples should set `env.num_gpus=0` or otherwise avoid assuming CUDA. Some tests and examples use `env.num_gpus=-1` to auto-select available GPUs, but that can be surprising in constrained environments.

## Column Types

Frequently useful `column_types` values:

- `text`: natural-language string columns.
- `text_ner`: the token/span source column for NER.
- `categorical`: category-like string columns.
- `numerical`: numeric features.
- `image_path`: local image file paths.
- `image_bytearray` and `image_base64_str`: image bytes/base64 columns.
- `document`: document images or PDFs handled by document models.

For object detection and semantic segmentation, prefer the task-specific format notes in `data-formats.md` and `object-detection.md` because the label is structured rather than a scalar target.
