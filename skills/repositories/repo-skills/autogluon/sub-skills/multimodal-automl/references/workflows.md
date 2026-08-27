# MultiModal Workflows

## Standard Text, Image, Document, or Mixed-Modality Prediction

Use this pattern for classification or regression when the data is not structured-only tabular. If the prompt contains only ordinary tabular columns and no text/image/document foundation-model need, route to `../tabular-ml/`.

```python
from autogluon.multimodal import MultiModalPredictor

predictor = MultiModalPredictor(
    label="target",
    problem_type="classification",  # or "binary", "multiclass", "regression"
    eval_metric="accuracy",
    path="automm_model",
)

predictor.fit(
    train_data=train_df,
    tuning_data=valid_df,
    presets="medium_quality",
    time_limit=600,
    column_types={
        "title": "text",
        "photo": "image_path",
        "price": "numerical",
        "category": "categorical",
    },
    hyperparameters={
        "env.num_gpus": 0,
        "env.num_workers": 0,
        "env.num_workers_inference": 0,
    },
)

pred = predictor.predict(test_df)
proba = predictor.predict_proba(test_df)
score = predictor.evaluate(test_df)
predictor.save("automm_model", standalone=True)
```

Guidance:

- Use `problem_type="binary"`, `"multiclass"`, or `"regression"` when the label semantics are known; use `"classification"` only when AutoGluon should resolve binary vs multiclass.
- Pass `column_types` when image paths look like text, IDs look categorical, or multiple text columns exist for NER.
- Set `path` in the constructor or `save_path` in `fit` for repeatable artifacts.
- Use smaller backbones or CPU-safe hyperparameters for local smoke runs; large pretrained checkpoints can trigger downloads and long training.

## Document Classification

Document prediction uses document foundation models and may need OCR/PDF system dependencies. Keep document files local and validate paths before training.

```python
predictor = MultiModalPredictor(
    label="label",
    problem_type="classification",
    hyperparameters={
        "model.document_transformer.checkpoint_name": "microsoft/layoutlmv3-base",
        "env.num_gpus": 0,
    },
)

predictor.fit(
    train_data=document_df,
    column_types={"document_path": "document"},
    time_limit=600,
)
embeddings = predictor.extract_embedding(document_df.drop(columns=["label"]))
```

Use `column_types` if the document column is ambiguous. For PDFs, ensure the user's environment has the document conversion/OCR stack described in `troubleshooting.md`.

## Named Entity Recognition

NER requires a text source column and an annotation label column. If there are multiple text columns, mark the entity source column as `text_ner`.

```python
predictor = MultiModalPredictor(problem_type="ner", label="entity_annotations")
predictor.fit(
    train_data=train_df,
    column_types={"text_snippet": "text_ner"},
    hyperparameters={"model.ner_text.checkpoint_name": "google/electra-small-discriminator"},
    time_limit=600,
)
entities = predictor.predict(test_df)
entity_scores = predictor.predict_proba(test_df)
```

Annotation strings commonly use JSON lists of spans such as `[{"entity_group": "B-ORG", "start": 0, "end": 2}]`. Validate that offsets match the exact text string and that the label column is excluded from prediction data.

## Semantic Matching on Paired Rows

Use matching problem types when rows contain query/response pairs and a binary or numeric similarity label.

```python
matcher = MultiModalPredictor(
    problem_type="text_similarity",
    query="premise",
    response="hypothesis",
    label="label",
    match_label=1,
    eval_metric="roc_auc",
)

matcher.fit(
    train_data=pair_df,
    tuning_data=valid_pair_df,
    time_limit=600,
    hyperparameters={"env.num_gpus": 0},
)

pair_scores = matcher.predict_proba(test_pair_df)
metrics = matcher.evaluate(test_pair_df)
```

Use `problem_type="image_similarity"` for image-image pairs and `"image_text_similarity"` for text-image pairs. In image-text matching, either side can be query or response, but the DataFrame column names must match the constructor.

## Semantic Search with Candidates and ID Mappings

When the pair table stores IDs rather than raw text/image content, provide `id_mappings` for both sides. This is the key repair pattern for prompts involving `query`, `response`, `match_label`, `candidate_data`, or retrieval IDs.

```python
id_mappings = {
    "query_id": query_df.set_index("query_id")["query_text"],
    "doc_id": doc_df.set_index("doc_id")["doc_text"],
}

matcher = MultiModalPredictor(
    problem_type="text_similarity",
    query="query_id",
    response="doc_id",
    label="relevance",
    match_label=1,
)
matcher.fit(train_data=judgments_df, id_mappings=id_mappings, time_limit=600)

hits = matcher.predict(
    data=query_df[["query_id"]],
    candidate_data=doc_df[["doc_id"]],
    id_mappings=id_mappings,
)
ranking_metrics = matcher.evaluate(
    data=judgments_df,
    query_data=query_df[["query_id"]],
    response_data=doc_df[["doc_id"]],
    id_mappings=id_mappings,
    cutoffs=[1, 5, 10],
)
```

Checklist for matching prompts:

- `query` and `response` must name columns present in the pair/evaluation data.
- `match_label` must be the positive class when labels are binary strings or integers.
- `candidate_data` is for retrieval candidates; it is not the same as validation/tuning data.
- `id_mappings` keys must match the ID column names and map IDs to the actual content values.
- For large candidate sets, tune `chunk_size` during `evaluate` to balance speed and memory.

## Zero-Shot and Feature Extraction

These modes can run without `fit` if checkpoints are available locally or network access is allowed.

```python
feature_extractor = MultiModalPredictor(
    problem_type="feature_extraction",
    hyperparameters={"model.hf_text.checkpoint_name": "sentence-transformers/all-MiniLM-L6-v2"},
)
embeddings = feature_extractor.extract_embedding(["first sentence", "second sentence"], as_tensor=True)

clip = MultiModalPredictor(problem_type="image_text_similarity")
scores = clip.predict_proba({"text": ["a photo of a dog"], "image": ["dog.jpg"]})
```

Feature extraction and zero-shot image/image-text tasks are often blocked by unavailable pretrained checkpoints. If the environment must be offline, ask for an already cached model or use a saved standalone predictor.

## Semantic Segmentation

Use a DataFrame with an image column and, for training/evaluation, a mask/label column. `sample_data_path` helps infer class/mask metadata.

```python
predictor = MultiModalPredictor(
    problem_type="semantic_segmentation",
    label="label",
    sample_data_path=train_df,
    eval_metric="iou",
    validation_metric="iou",
    hyperparameters={
        "model.sam.checkpoint_name": "facebook/sam-vit-base",
        "optim.peft": "lora",
        "env.precision": 32,
    },
)
predictor.fit(train_data=train_df, tuning_data=valid_df, time_limit=1200)
mask_predictions = predictor.predict(test_df, save_results=False)
metrics = predictor.evaluate(test_df, metrics=["iou"])
```

For binary masks, `num_classes=1` can be appropriate. For multi-class masks, confirm the mask encoding and `num_classes` inference before training.

## Object Detection

For object detection workflows, read `object-detection.md` before writing code. Minimal API shape:

```python
predictor = MultiModalPredictor(
    problem_type="object_detection",
    sample_data_path=train_annotation_or_df,
    hyperparameters={
        "model.mmdet_image.checkpoint_name": "yolov3_mobilenetv2_8xb24-320-300e_coco",
        "env.num_gpus": 0,
    },
)
predictor.fit(train_annotation_or_df, time_limit=1200)
metrics = predictor.evaluate(test_annotation_or_df)
predictions = predictor.predict(test_images_or_annotation, as_pandas=True)
```

Detection is more likely than basic text/image classification to require optional packages, GPU-compatible wheels, and local COCO/VOC annotations.

## Continuous Training and Distillation

`fit` can be called again on a loaded predictor for compatible data. Use this only when the new data has the same task semantics and compatible classes. For distillation, pass `teacher_predictor` or teacher predictions/labels when the user explicitly asks to compress or transfer knowledge.

## Save and Load

```python
predictor.save("model_dir", standalone=True)
loaded = MultiModalPredictor.load("model_dir")
```

Safety notes:

- `load` uses pickle-backed artifacts; never load untrusted predictor directories.
- `standalone=True` packages model assets for offline deployment when possible.
- `standalone=False` may require network/model-hub access later.
- Use `resume=True` only to resume interrupted training from a checkpoint.
