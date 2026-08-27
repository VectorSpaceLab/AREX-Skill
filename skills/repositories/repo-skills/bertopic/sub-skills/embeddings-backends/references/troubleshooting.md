# Troubleshooting

## Import and installation failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError` when importing BERTopic or a backend module | The base scientific stack is incomplete, or the optional backend extra is missing | Repair the environment first; then rerun the inventory script to see which backend family is still missing. |
| A `NotInstalled` placeholder raises `ModuleNotFoundError` for `OpenAIBackend`, `CohereBackend`, `MultiModalBackend`, `Model2VecBackend`, `FastEmbedBackend`, or `LangChainBackend` | The matching optional extra is not installed | Install the named extra and stop trying to instantiate the placeholder. |
| A string model id begins downloading when you wanted an offline path | `SentenceTransformerBackend` or language auto-selection is instantiating a model from a string | Pass a local backend object or use `embedding_model=None` with precomputed embeddings. |
| `HFTransformerBackend`, `FlairBackend`, `SpacyBackend`, `USEBackend`, `GensimBackend`, or `LangChainBackend` rejects the input object | The wrapper expects a specific object type, not a model name string | Load the native object first and pass that object into the wrapper. |
| `Model2VecBackend(distill=True)` fails immediately | The distillation extra is missing or the source model is not a string | Install `model2vec[distill]` and pass a string source model. |

## API misuse and invalid input

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ValueError` about embedding shape or row count | The matrix is not 2D, or its row count does not match the document list | Rebuild the embeddings so that each row maps to one document. |
| `fit_transform(..., embeddings=...)` still behaves like it wants a backend | `embedding_model` was not `None`, so backend selection still ran | Use `embedding_model=None` for a pure precomputed path. |
| `MultiModalBackend` mixes up samples | The documents and images lists are not aligned row-for-row | Keep both lists in the same order and the same length. |
| `SklearnEmbedder` does not update online | The wrapped base `Pipeline` does not support `.partial_fit()` | Use a pipeline designed for incremental learning or avoid online updates for that backend. |
| `FastEmbedBackend` raises a model error | The requested model is not in `TextEmbedding.list_supported_models()` | Choose a supported model name rather than a guess. |
| `GensimBackend` returns all-zero rows | The document tokens are out of vocabulary | Check tokenization and vocabulary coverage. |
| `SpacyBackend` gives a poor embedding or a tensor error | The loaded model has no standard vectors and no transformer tensor path | Load a model with vectors or use a transformer-capable spaCy pipeline. |

## Backend-specific gotchas

- `OpenAIBackend` and `CohereBackend` support batching and delay, but they still need live API access; they are not offline wrappers.
- `MultiModalBackend` truncates long text to 77 tokens when the tokenizer is available.
- `Model2VecBackend` distills only once per instance; create a new backend if you want a different vocabulary or distillation configuration.
- `select_backend(...)` uses type-based heuristics, so explicit backend objects are safer than guessing from a string when the task is ambiguous.
- If `sentence-transformers` is missing but you supplied `language=...`, BERTopic may fall back to `SklearnEmbedder`; install the intended package if that fallback is not acceptable.
- A missing base dependency such as `joblib` is not an embedding problem; fix the environment before chasing wrapper-specific bugs.

## Retry vs. stop

Retry with a smaller synthetic input if:

- the vocabulary is empty,
- the backend type was correct but the data shape was not, or
- a model-specific parameter was too aggressive.

Stop and repair the environment if:

- the package import stack is missing,
- a `NotInstalled` placeholder is raised, or
- you passed a string model id while the workflow must remain offline.
