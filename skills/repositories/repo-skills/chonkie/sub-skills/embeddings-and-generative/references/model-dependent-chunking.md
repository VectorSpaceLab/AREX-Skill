# Model-dependent chunking and refinement

Chonkie model-dependent workflows are optional surfaces. They can be powerful, but they introduce dependencies that deterministic chunkers do not: model packages, model downloads/cache, accelerator selection, provider credentials, provider quotas, and network timeouts. Do not use them as an invisible default when the user asked for offline or deterministic processing.

For deterministic alternatives, use `../chunking-and-types/`. For pipeline composition, use `../pipelines-and-processing/`. For vector DB write targets after embeddings are attached, use `../integrations-and-storage/`.

## `EmbeddingsRefinery`

Constructor signature: `EmbeddingsRefinery(embedding_model="minishlab/potion-retrieval-32M", **kwargs)`.

Purpose: attach an embedding vector to each existing `Chunk` by embedding `chunk.text` with `embedding_model.embed_batch`.

Typical direct use:

```python
from chonkie import RecursiveChunker, EmbeddingsRefinery

chunks = RecursiveChunker(tokenizer="character", chunk_size=512).chunk(text)
refinery = EmbeddingsRefinery(embedding_model="minishlab/potion-retrieval-32M")
chunks_with_vectors = refinery.refine(chunks)
vector_width = refinery.dimension
```

Notes:

- A string model is resolved through `AutoEmbeddings.get_embeddings`; all AutoEmbeddings fallback/download caveats apply.
- Passing an already-created `BaseEmbeddings` instance is the safest way to control credentials, offline settings, and model/device selection.
- `refine(chunks)` mutates each `Chunk` by assigning `chunk.embedding`; keep this in mind when reusing chunk objects.
- If the next step is vector storage, route storage-specific collection/index/service handling to `../integrations-and-storage/`.
- In a Chonkie `Pipeline`, use the pipeline sub-skill to place the refinery after chunking and before export/storage.

## `SemanticChunker`

Constructor signature: `SemanticChunker(embedding_model="minishlab/potion-base-32M", threshold=0.8, chunk_size=2048, similarity_window=3, min_sentences_per_chunk=1, min_characters_per_sentence=24, delim=[". ", "! ", "? ", "\n"], include_delim="prev", skip_window=0, filter_window=5, filter_polyorder=3, filter_tolerance=0.2, **kwargs)`.

Purpose: split text where sentence/window embeddings indicate semantic boundaries. It uses window embeddings and local-minimum filtering, then enforces `chunk_size` by splitting oversized groups.

Key parameters:

| Parameter | Meaning | Validation/operating note |
| --- | --- | --- |
| `embedding_model` | String resolved by `AutoEmbeddings`, or a `BaseEmbeddings` instance. | Use a concrete instance to avoid hidden fallback/download behavior. |
| `threshold` | Boundary filtering threshold. | Must be between 0 and 1, exclusive. Higher values generally allow fewer or stronger split points. |
| `chunk_size` | Maximum token count per chunk. | Must be positive. Oversized semantic groups are split by sentence to respect it. |
| `similarity_window` | Number of sentences in a comparison window. | Must be positive. If text has too few sentences, Chonkie returns one chunk. |
| `skip_window` | Optional merge window for similar non-consecutive groups. | `0` disables it; must be non-negative. |
| `filter_window`, `filter_polyorder`, `filter_tolerance` | Local-minimum smoothing/filter controls. | `filter_polyorder` must be non-negative and less than `filter_window`; tolerance is between 0 and 1. |
| `delim`, `include_delim`, `min_characters_per_sentence` | Sentence splitting controls. | Use deterministic chunker guidance for delimiter/type details. |

Operational example with an explicit embedding object:

```python
from chonkie import SemanticChunker
from chonkie.embeddings import Model2VecEmbeddings

embeddings = Model2VecEmbeddings("minishlab/potion-base-32M")
chunker = SemanticChunker(
    embedding_model=embeddings,
    threshold=0.8,
    chunk_size=512,
    similarity_window=3,
)
chunks = chunker.chunk(text)
```

Fallback plan:

- If `model2vec`/model cache is unavailable and no download is allowed, use `RecursiveChunker` or `SentenceChunker` from `../chunking-and-types/`.
- If the user only needs embeddings for downstream retrieval, deterministic chunk first and run `EmbeddingsRefinery` later when the embedding dependency is available.

## `LateChunker`

Constructor signature: `LateChunker(embedding_model="nomic-ai/modernbert-embed-base", chunk_size=2048, rules=RecursiveRules(), min_characters_per_chunk=24, **kwargs)`.

Purpose: recursively split text first, compute token-level embeddings for the full text, then average token embeddings into chunk embeddings. Returned `Chunk` objects include `embedding` values.

Requirements and behavior:

- Requires `SentenceTransformerEmbeddings`; string models instantiate `SentenceTransformerEmbeddings(model=embedding_model, **kwargs)`.
- The default model may require a model download and substantial memory. For lighter or already-cached operation, pass an existing `SentenceTransformerEmbeddings` instance or a known local model path.
- Uses the embedding model tokenizer for recursive token counts.
- If token-level embeddings are not available from the model, the implementation can fall back to sentence embeddings for chunks.
- `from_recipe(name="default", lang="en", path=None, ...)` can build recursive rules before late embedding. Recipe/network/cache decisions belong to deterministic chunking guidance.

Example:

```python
from chonkie import LateChunker
from chonkie.embeddings import SentenceTransformerEmbeddings

emb = SentenceTransformerEmbeddings("sentence-transformers/all-MiniLM-L6-v2")
chunker = LateChunker(embedding_model=emb, chunk_size=512)
chunks_with_embeddings = chunker.chunk(text)
```

Fallback plan:

- If `sentence_transformers` is not installed or the model cannot be loaded, use deterministic `RecursiveChunker` and defer embeddings.
- If token-level embedding memory is too high, chunk deterministically first, then use `EmbeddingsRefinery` with batch sizing appropriate to the model/provider.

## `NeuralChunker`

Constructor signature: `NeuralChunker(model="mirth/chonky_distilbert_base_uncased_1", tokenizer=None, device_map="auto", min_characters_per_chunk=10, stride=None)`.

Purpose: use a token-classification model to predict split points.

Supported bundled model identifiers:

| Model | Default stride |
| --- | --- |
| `mirth/chonky_distilbert_base_uncased_1` | 256 |
| `mirth/chonky_modernbert_base_1` | 512 |
| `mirth/chonky_modernbert_large_1` | 512 |

Requirements and behavior:

- Install gate: `chonkie[neural]` (`transformers` and `torch`).
- String model/tokenizer identifiers are loaded with Transformers and may download from a model hub.
- `device_map="auto"` may select CPU, CUDA, MPS, or another backend depending on the installed Transformers/Torch stack. Do not claim GPU/accelerator behavior unless verified in the current environment.
- Custom model objects must be compatible with Transformers token-classification; custom tokenizer objects must be compatible with `PreTrainedTokenizerFast` behavior.
- The chunker merges split spans that are closer than `min_characters_per_chunk`, then emits contiguous chunks.

Example:

```python
from chonkie import NeuralChunker

chunker = NeuralChunker(
    model="mirth/chonky_distilbert_base_uncased_1",
    device_map="cpu",  # choose explicitly when deterministic host selection matters
    min_characters_per_chunk=24,
)
chunks = chunker.chunk(text)
```

Fallback plan:

- If `transformers` or model weights are unavailable, use `RecursiveChunker`/`SentenceChunker` and record that neural segmentation was skipped.
- If output boundaries are unstable across model/device versions, add a deterministic post-check that chunks reconstruct the original text and meet minimum length constraints.

## `SlumberChunker`

Constructor signature: `SlumberChunker(genie=None, tokenizer="character", chunk_size=2048, rules=None, candidate_size=128, min_characters_per_chunk=24, extract_mode="auto", max_retries=3, verbose=True)`.

Purpose: recursively split text into candidates, ask a `BaseGenie` where topical boundaries should occur, and return Chonkie `Chunk` objects for the chosen ranges.

Requirements and behavior:

- If `genie` is omitted, Chonkie constructs `GeminiGenie()`, which requires Gemini credentials and package dependencies. Do not omit `genie` in offline or no-credential contexts.
- `extract_mode="auto"` uses JSON mode when the genie overrides `generate_json`; otherwise it uses plain text mode.
- `extract_mode="json"` requires Pydantic and a genie that supports structured JSON output.
- Text mode parses an integer from the generated response; invalid or out-of-bounds responses are retried up to `max_retries`, then Chonkie keeps the current passage group together.
- `verbose=True` displays a progress bar. Use `verbose=False` in scripts, tests, or logs where progress output is noisy.
- LLM calls are inherently nondeterministic unless the chosen provider/model/client supports and applies deterministic settings. The Chonkie constructor does not expose a universal temperature/seed knob.

Offline mocked example:

```python
from chonkie import BaseGenie, SlumberChunker

class StaticSplitGenie(BaseGenie):
    def generate(self, prompt: str) -> str:
        return "2"  # first split index for each candidate group

chunker = SlumberChunker(
    genie=StaticSplitGenie(),
    tokenizer="character",
    chunk_size=512,
    extract_mode="text",
    verbose=False,
)
chunks = chunker.chunk(text)
```

Provider example:

```python
from chonkie import OpenAIGenie, SlumberChunker

genie = OpenAIGenie(model="gpt-4.1", api_key="...")
chunker = SlumberChunker(genie=genie, extract_mode="json", verbose=False)
chunks = chunker.chunk(text)
```

Fallback plan:

- If provider credentials are absent, use a deterministic chunker or a test/mock `BaseGenie` only for development.
- If JSON generation fails, try `extract_mode="text"` or use a genie/provider known to support structured output.
- If costs/latency are high, reduce `chunk_size`/candidate count only after checking that boundaries remain useful; otherwise choose `SemanticChunker` or deterministic chunking.

## Choosing a workflow

1. **Need chunk text offline with no downloads?** Use deterministic chunkers from `../chunking-and-types/`.
2. **Need topic-aware chunks and local model downloads/cache are allowed?** Use `SemanticChunker` with `Model2VecEmbeddings` or a supplied `BaseEmbeddings`.
3. **Need chunk embeddings aligned to a sentence-transformers model?** Use `LateChunker` if token-level embeddings are important; otherwise chunk first and use `EmbeddingsRefinery`.
4. **Need learned segmentation from Chonkie-supported models?** Use `NeuralChunker` after verifying `transformers`, `torch`, and model cache/device behavior.
5. **Need LLM-guided topical boundaries?** Use `SlumberChunker` with an explicit `BaseGenie`; document credentials, provider, retry behavior, and nondeterminism.
6. **Need vector search ingestion?** Produce chunks here or in `../pipelines-and-processing/`, attach embeddings with `EmbeddingsRefinery`, then route storage to `../integrations-and-storage/`.
