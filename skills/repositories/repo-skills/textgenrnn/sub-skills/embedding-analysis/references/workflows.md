# Embedding analysis workflows

These recipes are self-contained and use the public `from textgenrnn import
textgenrnn` import. They do not require notebooks, plotting libraries, or access
to the original repository checkout.

If imports fail, first resolve the TensorFlow/Keras/setuptools stack using
[installation-and-compatibility](../../../references/installation-and-compatibility.md).

## 1. Encode raw attention vectors safely

Use raw vectors for one text, small text lists, smoke tests, and downstream code
that will choose its own dimensionality reduction.

```python
from textgenrnn import textgenrnn

textgen = textgenrnn()
texts = [
    "Never gonna give you up",
    "Never gonna let you down",
    "A totally different sentence",
]

vectors = textgen.encode_text_vectors(texts, pca_dims=None)
print(vectors.shape)  # pretrained default model: (3, 356)
```

Checklist:

- `vectors.shape[0] == len(texts)`.
- `vectors.ndim == 2`.
- For the bundled pretrained model, `vectors.shape[1] == 356`.
- Do not expect characters beyond the model's `max_length - 1` window to affect
  the vector.

## 2. Encode one query text

A single string is accepted, but PCA must be disabled because PCA cannot be fit
on one sample.

```python
query_raw = textgen.encode_text_vectors("What is love?", pca_dims=None)
print(query_raw.shape)  # (1, raw_vector_width)
```

If this fails with a PCA/sample error, confirm `pca_dims=None` was passed.

## 3. Fit reusable PCA for a candidate set

Use this pattern when a user wants a stable candidate vector table plus the same
projection for later query texts.

```python
from sklearn.metrics.pairwise import cosine_similarity

candidate_texts = [
    "Never gonna give you up, never gonna let you down",
    "Never gonna run around and desert you",
    "Never gonna make you cry, never gonna say goodbye",
    "Never gonna tell a lie and hurt you",
]

pca_dims = min(4, len(candidate_texts))
candidate_vectors, pca = textgen.encode_text_vectors(
    candidate_texts,
    pca_dims=pca_dims,
    return_pca=True,
)

query_raw = textgen.encode_text_vectors("Never gonna give", pca_dims=None)
query_vector = pca.transform(query_raw)

scores = cosine_similarity(query_vector, candidate_vectors)[0]
ranked = sorted(zip(candidate_texts, scores), key=lambda pair: -pair[1])
print(ranked[:3])
```

Rules:

- Choose `pca_dims <= min(len(candidate_texts), raw_vector_width)`.
- For fewer than 50 texts, never rely on the library's default `pca_dims=50`.
- Reuse PCA only with raw vectors from the same textgenrnn model/config.
- Validate query shape before transforming: it should be `(1, raw_vector_width)`.

## 4. Rank nearest texts with the built-in helper

For short candidate lists, disable PCA in `similarity`.

```python
pairs = textgen.similarity(
    "Never gonna give",
    candidate_texts,
    use_pca=False,
)
for candidate, score in pairs[:5]:
    print(f"{score: .4f}\t{candidate}")
```

Use `use_pca=True` only when the candidate list is large enough for the default
PCA dimension, or when you have verified the active package/scikit-learn
combination accepts the requested candidate count. For explicit PCA dimensions
or transform reuse, prefer the manual PCA workflow above.

## 5. Produce t-SNE coordinates for visualization

Use t-SNE when the goal is a 2D/3D visualization of a batch of texts, not when a
future query needs to be embedded into the same coordinates.

```python
coords = textgen.encode_text_vectors(
    many_texts,
    pca_dims=min(50, len(many_texts)),
    tsne_dims=2,
    tsne_seed=123,
)
print(coords.shape)  # (len(many_texts), 2)
```

Practical notes:

- Use enough samples for scikit-learn t-SNE's perplexity requirements. Very
  small smoke lists often fail.
- Set `tsne_seed` for repeatable coordinates.
- Save both input texts and coordinates together so plot labels remain aligned.
- Do not call a `transform` method on the returned t-SNE object for new texts;
  scikit-learn t-SNE does not support that reuse pattern.

## 6. Load a custom trained model for vector analysis

When the user already has a trained textgenrnn model triplet, construct the
model with matching files, then use the same vector APIs:

```python
textgen = textgenrnn(
    weights_path="my_model_weights.hdf5",
    vocab_path="my_model_vocab.json",
    config_path="my_model_config.json",
)
custom_vectors = textgen.encode_text_vectors(my_texts, pca_dims=None)
```

If the user needs to create that trained model, route to
[training](../../training/SKILL.md). If the user only needs generation from a
loaded model, route to [generation](../../generation/SKILL.md).

## 7. Use the bundled smoke helper

The smoke helper is safe by default: it disables PCA and t-SNE unless explicitly
requested.

```bash
python sub-skills/embedding-analysis/scripts/smoke_encode.py --help
python sub-skills/embedding-analysis/scripts/smoke_encode.py
python sub-skills/embedding-analysis/scripts/smoke_encode.py \
  --texts "alpha beta" --texts "alpha gamma" --texts "unrelated" \
  --similarity-query "alpha" --use-pca
```

If the `--use-pca` example fails on a small candidate list, rerun without
`--use-pca` or provide a larger candidate list. If `--pca-dims` fails, choose a
smaller value or omit it for raw vectors.

## 8. Shape guard before plotting or indexing

Use this guard when preparing arrays for plots, vector databases, or pairwise
metrics:

```python
vectors = textgen.encode_text_vectors(texts, pca_dims=None)
if vectors.ndim != 2:
    raise ValueError(f"Expected a 2D matrix, got shape {vectors.shape}")
if vectors.shape[0] != len(texts):
    raise ValueError("Vector row count does not match text count")
if vectors.shape[1] == 0:
    raise ValueError("Vector width is empty")
```

For plotting, reduce to two dimensions with PCA or t-SNE only after the raw
shape checks pass.
