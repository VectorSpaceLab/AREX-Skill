# Embedding analysis troubleshooting

Use this file for `encode_text_vectors`, PCA/t-SNE, and `similarity` failures.
For import, TensorFlow/Keras, or setuptools issues, use
[installation-and-compatibility](../../../references/installation-and-compatibility.md).

| Symptom | Likely cause | Concrete fix |
| --- | --- | --- |
| `ModuleNotFoundError` involving `tensorflow.compat.v1.keras` | Runtime uses a Keras 3 / recent TensorFlow stack that no longer exposes the compatibility API used by textgenrnn 2.0.0. | Use a pre-Keras-3 TensorFlow stack such as TensorFlow 2.15.x with matching Keras. See [installation-and-compatibility](../../../references/installation-and-compatibility.md). |
| `ModuleNotFoundError: No module named 'pkg_resources'` | `pkg_resources` is unavailable because setuptools is too new or not installed in the runtime. | Install or pin setuptools so `pkg_resources` is provided, for example with a `<81` setuptools version. See [installation-and-compatibility](../../../references/installation-and-compatibility.md). |
| `AssertionError: Must use more than 1 text for PCA` | `encode_text_vectors` was called on one text while PCA was enabled. | Pass `pca_dims=None` for one string: `textgen.encode_text_vectors("query", pca_dims=None)`. |
| Error like `n_components=50 must be between ...` | Default `pca_dims=50` is too large for the number of candidate texts under the active scikit-learn version. | Set `pca_dims=None` for raw vectors, or choose `pca_dims <= min(len(texts), raw_vector_width)`. For fewer than 50 texts, do not rely on the default. |
| `similarity(..., use_pca=True)` fails on a short candidate list | `similarity` fits candidate vectors with default PCA before comparing the query. | Use `similarity(query, texts, use_pca=False)` for small lists, or fit PCA manually with a safe `pca_dims` value and compute cosine similarity yourself. |
| `UnboundLocalError` mentioning `pca` | `return_pca=True` was used while no PCA object was fitted, usually with `pca_dims=None`. | Only use `return_pca=True` when `pca_dims` is an integer that can be fitted. If you need raw vectors, do not request `return_pca`. |
| `UnboundLocalError` mentioning `tsne` | `return_tsne=True` was used while `tsne_dims=None`. | Set `tsne_dims=2` or `3` when requesting `return_tsne`, or do not request the t-SNE object. |
| t-SNE error about perplexity and number of samples | The text list is too small for scikit-learn t-SNE defaults. | Increase the number of texts substantially or skip t-SNE for smoke tests. Use raw vectors or PCA for small lists. |
| t-SNE results move between runs | t-SNE has random initialization and optimization. | Pass a fixed integer `tsne_seed`, save the input text order with the coordinates, and avoid comparing coordinates across different batches. |
| Code tries `tsne.transform(new_vectors)` and fails | scikit-learn t-SNE is not a reusable transformer for new samples. | Use PCA for reusable projections. For new texts, encode raw vectors then call `pca.transform(...)` on a PCA object fitted to the candidate set. |
| `ValueError` or incorrect cosine-similarity shape | Query vector and candidate vectors were produced in different spaces, e.g. raw query vs PCA candidates. | Encode query raw with `pca_dims=None`, then transform it with the same fitted PCA used for candidates before computing similarity. Validate both arrays are 2D and have equal column counts. |
| Output vectors have unexpected width | A custom model config changes architecture dimensions, or PCA/t-SNE reduction was enabled. | For raw width checks, call `encode_text_vectors(..., pca_dims=None)`. Review the loaded model architecture in [model overview](../../../references/model-overview.md). |
| Long strings that differ near the end produce similar vectors | textgenrnn encodes only tokens inside the configured `max_length` window. | Compare prefixes inside the window, or train/use a model with larger `max_length` or word-level behavior via [training](../../training/SKILL.md). |
| Similarity rankings seem poor for a domain corpus | The bundled pretrained model was not trained for the user's domain or long semantic matching. | Treat rankings as model-specific attention-vector similarity, not universal sentence embeddings. If domain representation matters, train or fine-tune a model through [training](../../training/SKILL.md). |
| TensorFlow prints CUDA warnings on a CPU run | Host GPU/CUDA libraries are not fully available, but embedding inference can run on CPU. | Ignore if vectors are produced. GPU is optional acceleration for selected textgenrnn behavior. Use root compatibility guidance only if imports or model execution fail. |
| Helper script cannot import `textgenrnn` from an arbitrary directory | The active Python environment does not have textgenrnn installed. | Activate or select a compatible environment with textgenrnn installed, then rerun the helper. See [installation-and-compatibility](../../../references/installation-and-compatibility.md). |

## Quick fixes by task

### One string to raw vector

```python
vector = textgen.encode_text_vectors("query", pca_dims=None)
```

### Short list nearest-neighbor ranking

```python
pairs = textgen.similarity("query", candidates, use_pca=False)
```

### Reusable PCA candidate table

```python
pca_dims = min(10, len(candidates))
candidate_vectors, pca = textgen.encode_text_vectors(
    candidates,
    pca_dims=pca_dims,
    return_pca=True,
)
query_raw = textgen.encode_text_vectors("query", pca_dims=None)
query_vector = pca.transform(query_raw)
```

### t-SNE visualization batch

```python
coords = textgen.encode_text_vectors(
    many_texts,
    pca_dims=min(50, len(many_texts)),
    tsne_dims=2,
    tsne_seed=123,
)
```

If this fails on sample count, use more texts or omit `tsne_dims`.
