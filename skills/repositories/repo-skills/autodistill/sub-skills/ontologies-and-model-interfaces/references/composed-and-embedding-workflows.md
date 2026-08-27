# Composed and Embedding Workflows

Read this when a task asks to combine detector and classifier models, refine detections with a second model, use image/text embeddings, or reconcile public docs with the source snapshot.

## Composed Detection + Classification

The source class in this snapshot is:

```python
from autodistill.core.composed_detection_model import ComposedDetectionModel
```

A composed model runs:

1. `detection_model.predict(image)` to get `supervision.Detections`.
2. For each bounding box, crop the source image into a temporary file named `temp.jpeg`.
3. `classification_model.predict("temp.jpeg")` to classify the crop.
4. Replace the detection's `class_id` with the top classification result when available.

Basic shape:

```python
from autodistill.core.composed_detection_model import ComposedDetectionModel

model = ComposedDetectionModel(
    detection_model=my_detector,
    classification_model=my_classifier,
)
detections = model.predict("image.jpg")
```

Caveats:

- Some docs mention `CustomDetectionModel` or `CombinedDetectionModel`; those names are not the verified source class in this snapshot.
- `predict` expects an image path because it opens the image with Pillow and writes `temp.jpeg`.
- The temporary file name is fixed; avoid concurrent composed predictions in the same working directory unless the concrete implementation is changed.
- If the classification model returns no class ids for a crop, the original detection class id is left unchanged.

## Set-of-Marks Branch

If `set_of_marks` is not `None`, the composed model annotates detections with numeric marks and expects the classification model to expose a `set_of_marks(...)` method. If it does not, the source raises an exception naming supported models.

Only use this branch after verifying the concrete classification plugin supports set-of-marks inputs and understands the temporary marked image.

## Embedding Ontology Use

Embedding workflows are useful when text prompts alone are weak or when a classifier should compare images/regions against examples.

Core pieces:

```python
from autodistill.core import EmbeddingOntologyImage, EmbeddingOntologyRaw
from autodistill.core.embedding_ontology import compare_embeddings
```

`EmbeddingOntologyImage` accepts a mapping and uses an embedding model's `embed_image` during processing. `EmbeddingOntologyRaw` accepts precomputed embedding vectors. `compare_embeddings(image_embedding, comparison_embeddings, distance_metric="cosine")` returns `supervision.Classifications` for cosine similarity; other distance metrics raise `NotImplementedError`.

Caveats:

- Use the same embedding model/preprocessing for stored embeddings and runtime embeddings.
- Check vector shapes before comparing.
- `EmbeddingOntologyImage.process(model)` mutates the ontology's stored embeddings.
- Some embedding ontology methods in this source snapshot use list/tuple iteration patterns that may not match every mapping form; run a small conformance test before large labeling.

## When to Prefer Simpler Workflows

Use a normal detection base model if the detector can already produce the desired classes. Use composition when a detector localizes generic regions and a classifier adds fine-grained class labels. Use embeddings when examples are more reliable than text prompts.
