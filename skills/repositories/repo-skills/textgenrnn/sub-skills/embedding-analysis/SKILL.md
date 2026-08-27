---
name: embedding-analysis
description: "Guides agents using textgenrnn encode_text_vectors,
  attention-layer vectors, PCA/t-SNE, and similarity nearest-text analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# textgenrnn Embedding Analysis

Use this sub-skill when the task is to turn text strings into vectors with
textgenrnn's attention layer, reduce those vectors with PCA or t-SNE, or rank
candidate strings by cosine similarity.

## Route here for

- Calling `encode_text_vectors` on one string or a list of strings.
- Understanding raw attention-vector shape and why the default pretrained model
  returns 356 raw features before dimensionality reduction.
- Choosing `pca_dims`, `tsne_dims`, `tsne_seed`, `return_pca`, and
  `return_tsne` safely.
- Reusing a fitted PCA object to transform a later query vector into the same
  space as a candidate set.
- Calling `similarity(text, texts, use_pca=...)` for nearest-text ranking.
- Diagnosing PCA/t-SNE failures caused by too few texts, invalid dimensions, or
  shape mismatches.

## Route elsewhere

- Text generation, model loading for generation-only tasks, temperatures,
  prefixes, and output files: use [generation](../generation/SKILL.md).
- Training, fine-tuning, scratch model creation, context labels, word-level
  models, or changing `max_length`/representation capacity: use
  [training](../training/SKILL.md).
- Import, TensorFlow/Keras, `pkg_resources`, or package-version problems: use
  [root compatibility guidance](../../references/installation-and-compatibility.md).
- Architecture/config background, including why attention vectors have their
  size: use [root model overview](../../references/model-overview.md).

## First checks

1. Confirm the user has a textgenrnn-compatible runtime. The verified stack is a
   pre-Keras-3 TensorFlow/Keras stack such as TensorFlow 2.15.x with
   `pkg_resources` available. If imports fail, route to
   [installation and compatibility](../../references/installation-and-compatibility.md).
2. Ask whether the user wants raw attention vectors, PCA-reduced vectors,
   t-SNE coordinates for visualization, or nearest-text ranking.
3. Count the candidate texts before choosing PCA or t-SNE settings. Small lists
   need explicit dimensions or `pca_dims=None`.
4. Decide whether a fitted PCA object must be reused later. If yes, request
   `return_pca=True` while fitting candidate vectors, then transform new raw
   query vectors with that PCA object.

## Default-safe operating pattern

For small or unknown text counts, prefer raw vectors first:

```python
from textgenrnn import textgenrnn

textgen = textgenrnn()
texts = ["short example", "another example"]
vectors = textgen.encode_text_vectors(texts, pca_dims=None)
print(vectors.shape)
```

Then apply PCA only when the sample count supports the chosen dimension:

```python
candidate_vectors, pca = textgen.encode_text_vectors(
    texts,
    pca_dims=min(10, len(texts)),
    return_pca=True,
)
query_raw = textgen.encode_text_vectors("query text", pca_dims=None)
query_vector = pca.transform(query_raw)
```

For nearest-text ranking, avoid the library's PCA default unless there are
enough candidate texts for it:

```python
pairs = textgen.similarity("query text", texts, use_pca=False)
for candidate, score in pairs[:5]:
    print(score, candidate)
```

## Parameter decisions

- `pca_dims=None`: safest for one text or small candidate lists; returns raw
  attention vectors.
- `pca_dims=N`: use only when `N <= min(number_of_texts, raw_vector_width)`.
  In modern scikit-learn, `pca_dims=50` can fail on fewer than 50 texts.
- `return_pca=True`: valid only when PCA is actually fitted; do not combine it
  with `pca_dims=None`.
- `tsne_dims=N`: intended for visualization coordinates, usually `2` or `3`;
  requires enough samples for scikit-learn t-SNE's perplexity constraints.
- `tsne_seed=N`: use a fixed integer seed for repeatable t-SNE initialization.
- `return_tsne=True`: valid only when t-SNE is actually fitted; do not combine
  it with `tsne_dims=None`.
- `use_pca=False` in `similarity`: safest default for small candidate sets.
- `use_pca=True` in `similarity`: fits PCA on the candidate texts, transforms
  the query into that fitted space, then ranks by cosine similarity.

## Shape and truncation expectations

- A single input string is internally wrapped as a one-item list, so raw output
  shape is `(1, vector_width)`.
- The bundled pretrained model's raw attention width is 356.
- Custom trained models can have a different width if their architecture changes.
- Only the first `max_length - 1` text tokens influence vectors. The pretrained
  character-level model effectively uses the first 39 characters; train a model
  with a larger `max_length` or word-level configuration if that is not enough.
- PCA output shape is `(number_of_texts, pca_dims)` when the requested dimension
  is supported.
- t-SNE output shape is `(number_of_texts, tsne_dims)` when fitting succeeds.

## Bundled references and helper

- [API reference](references/api-reference.md): exact signatures, defaults, and
  parameter constraints.
- [Workflows](references/workflows.md): reusable recipes for raw vectors,
  PCA reuse, t-SNE coordinates, and similarity ranking.
- [Troubleshooting](references/troubleshooting.md): concrete fixes for
  PCA/t-SNE/sample-size/import/runtime failures.
- [Smoke helper](scripts/smoke_encode.py): safe command-line check that encodes
  sample texts and prints similarity rankings without depending on notebooks or
  plotting libraries.

## Do not

- Do not ask future agents to open notebooks or original repository files.
- Do not use PCA defaults blindly on small text sets.
- Do not treat t-SNE coordinates as reusable embeddings for new texts; t-SNE is
  a fitted visualization of a batch, not a stable transform for later queries.
- Do not retrain solely inside this sub-skill. If representation quality depends
  on new data, route to [training](../training/SKILL.md).
