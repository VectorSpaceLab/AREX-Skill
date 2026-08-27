# Embedding analysis API reference

This reference covers the public textgenrnn 2.0.0 embedding-analysis surface.
Use it with the package-level compatibility guidance in
[installation-and-compatibility](../../../references/installation-and-compatibility.md)
when imports or TensorFlow/Keras setup fail.

## Public import

```python
from textgenrnn import textgenrnn

textgen = textgenrnn()
```

`textgenrnn()` loads the bundled pretrained character-level model when no custom
weights, vocab, or config paths are supplied. Custom models produced by training
can also be analyzed, provided their matching weights/vocab/config are loaded
when constructing `textgenrnn`.

## `encode_text_vectors`

Verified signature:

```python
textgenrnn.encode_text_vectors(
    self,
    texts,
    pca_dims=50,
    tsne_dims=None,
    tsne_seed=None,
    return_pca=False,
    return_tsne=False,
)
```

### Inputs

| Parameter | Default | Notes |
| --- | --- | --- |
| `texts` | required | A single string or a list of strings. A single string is wrapped internally as a one-item list. |
| `pca_dims` | `50` | Number of PCA components to fit after raw vector extraction. Use `None` to return raw attention vectors. For modern scikit-learn, the requested value must not exceed `min(number_of_texts, raw_vector_width)`. |
| `tsne_dims` | `None` | Number of t-SNE coordinates to fit after raw extraction and after optional PCA. Usually `2` or `3`; requires enough samples for t-SNE perplexity. |
| `tsne_seed` | `None` | Integer random seed forwarded to t-SNE for repeatable initialization. |
| `return_pca` | `False` | When `True`, returns the fitted PCA object along with vectors. Only valid when PCA is fitted; do not set with `pca_dims=None`. |
| `return_tsne` | `False` | When `True`, returns the fitted t-SNE object along with vectors. Only valid when t-SNE is fitted; do not set with `tsne_dims=None`. |

### Processing order

1. Builds a temporary Keras model whose output is the model layer named
   `attention`.
2. Encodes each text into the model's configured sequence length.
3. Predicts one attention vector per text.
4. Applies PCA when `pca_dims is not None`.
5. Applies t-SNE when `tsne_dims is not None`.
6. Optionally appends fitted transform objects to the return value.

### Return shapes and objects

| Call pattern | Return value |
| --- | --- |
| `encode_text_vectors(texts, pca_dims=None)` | `numpy.ndarray` with shape `(n_texts, raw_vector_width)` |
| `encode_text_vectors("one text", pca_dims=None)` | `numpy.ndarray` with shape `(1, raw_vector_width)` |
| `encode_text_vectors(texts, pca_dims=N)` | `numpy.ndarray` with shape `(n_texts, N)` when PCA succeeds |
| `encode_text_vectors(texts, tsne_dims=N)` | `numpy.ndarray` with shape `(n_texts, N)` after PCA then t-SNE when both succeed |
| `encode_text_vectors(texts, return_pca=True)` | `[vectors, pca]` |
| `encode_text_vectors(texts, return_tsne=True, tsne_dims=N)` | `[vectors, tsne]` if PCA is not returned, or `[vectors, pca, tsne]` when both return flags are set |

The bundled pretrained model's raw attention vector width is 356. Custom models
can differ if `dim_embeddings`, `rnn_size`, `rnn_layers`, or bidirectionality
change. See the package-level [model overview](../../../references/model-overview.md)
for architecture/config background.

### Text truncation

The vector reflects only the tokens that fit the model's `max_length`. For the
bundled pretrained character-level model, only the first `max_length - 1` text
characters are represented, effectively the first 39 characters. Use a custom
trained model with a larger `max_length` or word-level configuration when the
analysis requires longer semantic context; route that work to
[training](../../training/SKILL.md).

### PCA constraints

- `pca_dims=None` is required for one text and is the safest choice for small
  batches.
- `pca_dims=50` is the library default, but it is not safe for fewer than 50
  texts under current scikit-learn behavior.
- Pick `pca_dims <= min(len(texts), raw_vector_width)`.
- If a later query must be compared in the same PCA space, fit PCA on the
  candidate set with `return_pca=True`, encode the query with `pca_dims=None`,
  then call `pca.transform(query_raw)`.

### t-SNE constraints

- t-SNE is batch visualization, not a stable encoder for future texts.
- Use `tsne_dims=2` or `3` for plotting coordinates.
- Use `tsne_seed=<int>` for reproducibility.
- The default scikit-learn t-SNE perplexity requires more samples than small
  smoke lists usually provide. If it fails, increase the number of texts or skip
  t-SNE in automated checks.
- The returned t-SNE object does not provide a reusable `transform` method for
  new text strings.

## `similarity`

Verified signature:

```python
textgenrnn.similarity(self, text, texts, use_pca=True)
```

### Inputs and behavior

| Parameter | Default | Notes |
| --- | --- | --- |
| `text` | required | Query string. It is encoded as one raw attention vector first. |
| `texts` | required | Candidate list of strings. Return pairs preserve these strings. |
| `use_pca` | `True` | When `True`, candidate vectors are encoded with default PCA and the query raw vector is transformed by the fitted PCA object. When `False`, raw vectors are compared directly. |

`similarity` returns a list of `(candidate_text, cosine_similarity_score)` pairs
sorted descending by score.

### Safer small-sample use

The default `use_pca=True` can fail when the candidate list is smaller than the
library's default PCA dimension. For a short list, prefer:

```python
pairs = textgen.similarity("query", candidates, use_pca=False)
```

For a larger candidate set where PCA is desired and reusable, call
`encode_text_vectors(..., return_pca=True)` directly, then transform query raw
vectors with the returned PCA object before computing cosine similarity.

## Related routes

- Loading custom weights/config/vocab just to generate text belongs in
  [generation](../../generation/SKILL.md).
- Training a representation model with larger `max_length`, word-level tokens,
  or new data belongs in [training](../../training/SKILL.md).
- Import/runtime failures belong in
  [installation and compatibility](../../../references/installation-and-compatibility.md).
