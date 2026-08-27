# MultiModal Data Formats

## General DataFrame Shape

Most `MultiModalPredictor.fit` calls use a pandas DataFrame. Prediction data should contain the same feature columns as training data, excluding the label column.

```python
train_df = pd.DataFrame({
    "title": ["red shirt", "blue shoe"],
    "description": ["cotton casual", "running sneaker"],
    "image": ["images/1.jpg", "images/2.jpg"],
    "price": [19.99, 59.99],
    "label": ["apparel", "footwear"],
})

column_types = {
    "title": "text",
    "description": "text",
    "image": "image_path",
    "price": "numerical",
}
```

Rules:

- Keep file paths local and readable from the current process.
- Do not include the label column in `predict` data unless the method explicitly accepts labels for evaluation.
- Use `column_types` when inference may mistake image/document paths or IDs for ordinary text/categorical columns.
- Use `../scripts/inspect_multimodal_inputs.py` to validate local paths and required columns before training.

## Column Types

| Type | Use for | Notes |
| --- | --- | --- |
| `text` | sentences, paragraphs, product titles, descriptions | Long text may be truncated by model max length. |
| `text_ner` | the source text column for NER | Needed when multiple text columns exist. |
| `categorical` | category strings or IDs used as features | Avoid using this for matching IDs that need `id_mappings`. |
| `numerical` | numeric scalar features | Non-numeric strings should be cleaned first. |
| `image_path` | local image file paths | Missing paths can become zero images or fail depending config. |
| `image_bytearray` | byte arrays containing encoded images | Useful when data is already loaded from storage. |
| `image_base64_str` | base64-encoded image strings | Validate decoding before training. |
| `document` | document image/PDF inputs for document models | May need OCR/PDF dependencies. |

## Image Inputs

Supported inference shapes include:

```python
predictor.predict("image.jpg")
predictor.predict(["image1.jpg", "image2.jpg"])
predictor.predict({"image": ["image1.jpg", "image2.jpg"]})
predictor.predict(pd.DataFrame({"image": ["image1.jpg", "image2.jpg"]}))
```

For training, prefer a DataFrame with an image path column and a scalar label for classification/regression, or task-specific labels for detection/segmentation. Validate that image files exist and have common extensions such as `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, or `.tif`.

## Document Inputs

Document classification can use scanned document images or PDFs through the document model family.

```python
document_df = pd.DataFrame({
    "document_path": ["docs/invoice_001.pdf", "docs/form_002.png"],
    "label": ["invoice", "form"],
})

predictor.fit(
    document_df,
    column_types={"document_path": "document"},
    hyperparameters={"model.document_transformer.checkpoint_name": "microsoft/layoutlmv3-base"},
)
```

Document workflows commonly require optional dependencies outside core AutoGluon, such as PDF conversion tools, OCR tools, and compatible transformer checkpoints. If a document path points to a remote URL, download it through a user-approved data step before passing it to AutoGluon.

## NER Inputs

NER uses one text source column plus a label column containing entity span annotations.

```python
ner_df = pd.DataFrame({
    "text_snippet": ["EU rejects German call to boycott British lamb ."],
    "entity_annotations": [
        '[{"entity_group": "B-ORG", "start": 0, "end": 2}, {"entity_group": "B-MISC", "start": 11, "end": 17}]'
    ],
})

predictor = MultiModalPredictor(problem_type="ner", label="entity_annotations")
predictor.fit(ner_df, column_types={"text_snippet": "text_ner"})
```

NER checks:

- Annotation JSON must parse to a list.
- `start` and `end` offsets must be integer character offsets into the exact source text.
- `entity_group` should follow the expected tag scheme, commonly BIO-style values such as `B-ORG`, `I-PER`, or `O`.
- If there are several text columns, exactly one should usually be marked `text_ner`.

## Semantic Matching Pair Data

Training pairs usually contain `query`, `response`, and a label.

```python
pairs = pd.DataFrame({
    "premise": ["A man is eating pasta."],
    "hypothesis": ["A person eats food."],
    "label": [1],
})

matcher = MultiModalPredictor(
    problem_type="text_similarity",
    query="premise",
    response="hypothesis",
    label="label",
    match_label=1,
)
```

For image-image matching, both columns are image paths. For image-text matching, one column is text and one is image paths. `match_label` is the positive label indicating that the two sides match.

## Semantic Search ID Mapping Data

Use `id_mappings` when pair rows contain identifiers instead of raw text/image values.

```python
judgments = pd.DataFrame({"query_id": ["q1"], "doc_id": ["d1"], "relevance": [1]})
queries = pd.DataFrame({"query_id": ["q1"], "query_text": ["refund policy"]})
docs = pd.DataFrame({"doc_id": ["d1"], "doc_text": ["How refunds work"]})

id_mappings = {
    "query_id": queries.set_index("query_id")["query_text"],
    "doc_id": docs.set_index("doc_id")["doc_text"],
}
```

`id_mappings` keys must be the ID column names used by `query` and `response`. Values can be dictionaries or pandas Series mapping each ID to its text/image content.

## Semantic Segmentation Data

Segmentation uses image paths and mask paths. The label column typically points to ground-truth mask images for fit/evaluate; prediction may omit labels.

```python
seg_train = pd.DataFrame({
    "image": ["train/images/0001.png"],
    "label": ["train/masks/0001.png"],
})
seg_test = pd.DataFrame({"image": ["test/images/0002.png"]})

predictor = MultiModalPredictor(
    problem_type="semantic_segmentation",
    label="label",
    sample_data_path=seg_train,
    num_classes=1,
)
```

Checks:

- Image and mask files should exist locally.
- Image/mask pairing should be deterministic and aligned row-by-row.
- Binary segmentation may use `num_classes=1`; multi-class masks should have a verified class count.
- Metrics include `iou`, `ber`, and `sm` depending on task type.

## Object Detection Data

Object detection supports COCO annotation JSON paths, VOC-style data after conversion, and DataFrames with image paths and RoIs. See `object-detection.md` for detailed schema checks.

## Local Validation Commands

Examples from inside this sub-skill directory:

```bash
python scripts/inspect_multimodal_inputs.py --csv train.csv --label label --image-columns image --text-columns title description
python scripts/inspect_multimodal_inputs.py --csv pairs.csv --query query_id --response doc_id --label relevance --id-map query_id=queries.csv:query_id:text --id-map doc_id=docs.csv:doc_id:text
python scripts/inspect_multimodal_inputs.py --coco annotations/instances_train.json --image-root images --check-images
python scripts/inspect_multimodal_inputs.py --voc-root VOCdevkit/VOC2007 --check-images
```

These commands inspect local metadata only. They do not train, download datasets, or import heavy model backends.
