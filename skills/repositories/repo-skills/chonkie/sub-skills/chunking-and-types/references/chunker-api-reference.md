# Chunker API reference

This reference is self-contained for Chonkie 1.7.0 public chunker APIs. All chunkers return `list[Chunk]` for a single string unless stated otherwise. A chunk has `text`, `start_index`, `end_index`, `token_count`, optional `context`, optional `embedding`, and `metadata`.

## Selection map

| Need | Prefer | Why | Route if out of scope |
| --- | --- | --- | --- |
| General local RAG/document chunking | `RecursiveChunker` | Splits paragraphs, sentences, punctuation, whitespace, then tokens; good default quality without models. | Pipeline placement: `../pipelines-and-processing/` |
| Strict chunk-size ceiling | `TokenChunker` | Splits encoded token windows and supports overlap. | Downstream storage/export: `../integrations-and-storage/` |
| Clean sentence boundaries | `SentenceChunker` | Uses sentence delimiters, minimum sentence lengths, and token budgets. | Pipeline placement: `../pipelines-and-processing/` |
| Maximum throughput / rough pre-splitting | `FastChunker` | Uses byte-size boundaries and SIMD core paths; `token_count` is intentionally `0`. | If retrieval quality matters, refine with recursive/sentence first. |
| Markdown/HTML tables | `TableChunker` | Preserves table header and chunks rows. | Table extraction from documents/chefs: `../pipelines-and-processing/` |
| Source code | `CodeChunker` | Uses tree-sitter language parsing to preserve functions/classes better than raw text splitting. | CLI/API code routes: `../interfaces-and-deployment/` |
| Topic-aware chunks from embeddings | `SemanticChunker` | Uses an embedding model and similarity minima. | Embedding dependencies/model choice: `../embeddings-and-generative/` |
| Retrieval chunks with embedded late-interaction vectors | `LateChunker` | Splits recursively, then averages token embeddings into chunk embeddings. | Embedding/model setup: `../embeddings-and-generative/` |
| Model-trained topic segmentation | `NeuralChunker` | Uses a transformers token-classification model. | Model download/device setup: `../embeddings-and-generative/` |
| LLM-guided high-quality splitting | `SlumberChunker` | Uses a Genie/generative model over candidate splits. | Provider/genie credentials: `../embeddings-and-generative/` |
| External TeraflopAI segmentation | `TeraflopAIChunker` | Sends text to TeraflopAI segmentation API and wraps segments as Chonkie chunks. | Credential/API setup: `../embeddings-and-generative/` |

## Deterministic required/local chunkers

These chunkers are the safe baseline. They need no provider credentials and no model downloads. They are appropriate for default smoke tests and offline work.

### `TokenChunker`

Constructor:

```python
TokenChunker(tokenizer="character", chunk_size=2048, chunk_overlap=0)
```

- `tokenizer`: a tokenizer name or object accepted by `AutoTokenizer`.
- `chunk_size`: positive maximum token count per chunk.
- `chunk_overlap`: integer tokens or float fraction of `chunk_size`; must be less than `chunk_size` after conversion.
- Empty/whitespace-only text returns `[]`.
- `chunk_batch(texts, batch_size=1, show_progress_bar=True)` processes batches; `__call__` accepts a string or list of strings.

Use when model context windows require a hard maximum token count. Use `chunk_overlap` for retrieval recall, but remember that overlapping windows mean concatenating chunk texts will duplicate overlap content.

Example:

```python
from chonkie import TokenChunker

chunker = TokenChunker(tokenizer="character", chunk_size=128, chunk_overlap=16)
chunks = chunker.chunk(text)
assert all(c.token_count <= 128 for c in chunks)
```

### `RecursiveChunker`

Constructor:

```python
RecursiveChunker(tokenizer="character", chunk_size=2048, rules=RecursiveRules(), min_characters_per_chunk=24)
```

- `chunk_size`: positive maximum token target.
- `rules`: a `RecursiveRules` object. Default rules split by paragraph breaks, sentence delimiters, punctuation/pauses, whitespace, then token windows.
- `min_characters_per_chunk`: positive minimum split size used while applying delimiter levels.
- `from_recipe(name="default", lang="en", path=None, ...)` loads rule recipes. Use a local `path` when offline or when deterministic recipe provenance matters.

Use as the first recommendation for most prose/markdown text. With default rules and no overlap, chunks reconstruct the original text by joining `chunk.text` in order.

Example:

```python
from chonkie import RecursiveChunker, RecursiveLevel, RecursiveRules

rules = RecursiveRules(levels=[
    RecursiveLevel(delimiters=["\n\n", "\n"]),
    RecursiveLevel(delimiters=[". ", "! ", "? "]),
    RecursiveLevel(whitespace=True),
    RecursiveLevel(),
])
chunker = RecursiveChunker(tokenizer="character", chunk_size=512, rules=rules)
chunks = chunker.chunk(text)
```

### `SentenceChunker`

Constructor:

```python
SentenceChunker(
    tokenizer="character",
    chunk_size=2048,
    chunk_overlap=0,
    min_sentences_per_chunk=1,
    min_characters_per_sentence=12,
    approximate=False,
    delim=[". ", "! ", "? ", "\n"],
    include_delim="prev",
)
```

- `chunk_overlap` is counted in tokens and must be less than `chunk_size`.
- `min_sentences_per_chunk` and `min_characters_per_sentence` must be at least `1`.
- `delim` can be a string or list of strings.
- `include_delim` is `"prev"`, `"next"`, or `None`; default keeps punctuation with the previous sentence.
- `approximate=True` is deprecated; prefer exact counting.
- `from_recipe(...)` can load delimiter recipes; prefer local recipe paths when network access is not available.

Use when sentence integrity is more important than strict chunk size. If a single sentence is longer than `chunk_size`, use `TokenChunker` for strict windows or `RecursiveChunker` for deeper fallback splitting.

### `FastChunker`

Constructor:

```python
FastChunker(chunk_size=4096, delimiters="\n.?", pattern=None, prefix=False, consecutive=False, forward_fallback=False)
```

- `chunk_size` is a byte target, not a token target.
- `delimiters` is a string of delimiter characters.
- `pattern` is an optional multi-byte pattern and overrides `delimiters`.
- `prefix=True` puts delimiter bytes at the start of the next chunk.
- `consecutive=True` splits at the start of consecutive delimiter runs.
- `forward_fallback=True` searches forward when no delimiter is found in the backward window.
- Returned chunks have `token_count == 0` by design.

Use for very high-throughput pre-splitting or bounded file scans. Do not use it when token counts or sentence/word boundaries are contractually required.

### `TableChunker`

Constructor:

```python
TableChunker(tokenizer="row", chunk_size=3)
```

- Default `"row"` tokenizer treats each table row as a token; `chunk_size` means data rows per output table chunk.
- For non-row tokenizers, `chunk_size` is a token budget and the table header/footer are counted.
- Markdown tables require at least a header, separator, and one data row.
- HTML tables are supported through plain row extraction; output chunks preserve the table wrapper/header where possible.
- When table content is already attached to a `MarkdownDocument`, `chunk_document()` offsets chunks back into the original document and preserves document metadata.

Use for table strings. If the task first needs to extract tables from raw markdown or files, route that extraction/chef work to `../pipelines-and-processing/` and return here for chunk sizing.

## Optional local parser chunker

### `CodeChunker`

Constructor:

```python
CodeChunker(tokenizer="character", chunk_size=2048, language="auto", include_nodes=False)
```

- Requires the `code` extra (`tree-sitter-language-pack`).
- `language="auto"` detects language but is slower; specify `"python"`, `"javascript"`, etc. when known.
- The constructor can initialize/download tree-sitter language grammars through its dependency. For deterministic/offline runs, verify the grammar cache first or provide an environment where grammars are already available.
- `chunk_size` is converted to an estimated byte budget for the parser.
- Empty or whitespace-only code returns `[]`.
- If parsing yields no structured chunks, the chunker returns one whole-file chunk.
- `chunk_document()` handles `MarkdownDocument.code` blocks and re-bases offsets into the full markdown document.

Example:

```python
from chonkie import CodeChunker

code = "def add(a, b):\n    return a + b\n"
chunker = CodeChunker(language="python", chunk_size=128)
chunks = chunker.chunk(code)
assert "".join(c.text for c in chunks) == code
```

If import or grammar initialization fails, fall back to `RecursiveChunker` for local deterministic chunking and explain that AST-aware code chunks need the `code` extra and a ready tree-sitter grammar cache.

## Optional model/provider/external chunkers

These chunkers are not part of the deterministic baseline. They may require optional extras, model caches/downloads, accelerators, provider credentials, or live network/API access. Keep a `RecursiveChunker` or `TokenChunker` fallback.

| Chunker | Constructor | Required gates | Notes |
| --- | --- | --- | --- |
| `SemanticChunker` | `SemanticChunker(embedding_model="minishlab/potion-base-32M", threshold=0.8, chunk_size=2048, similarity_window=3, min_sentences_per_chunk=1, min_characters_per_sentence=24, delim=[". ", "! ", "? ", "\n"], include_delim="prev", skip_window=0, filter_window=5, filter_polyorder=3, filter_tolerance=0.2, **kwargs)` | Embeddings extra/provider/model; model cache or network if using a model name. | Threshold must be between 0 and 1. Uses sentence/window embeddings and Savitzky-Golay minima. Route embedding setup to `../embeddings-and-generative/`. |
| `LateChunker` | `LateChunker(embedding_model="nomic-ai/modernbert-embed-base", chunk_size=2048, rules=RecursiveRules(), min_characters_per_chunk=24, **kwargs)` | Sentence-transformer extra (`st`) and model availability. | Extends recursive splitting and attaches `embedding` to returned chunks. |
| `NeuralChunker` | `NeuralChunker(model="mirth/chonky_distilbert_base_uncased_1", tokenizer=None, device_map="auto", min_characters_per_chunk=10, stride=None)` | `neural` extra, transformers/torch, supported model cache/download, device plan. | Supported model names are `mirth/chonky_distilbert_base_uncased_1`, `mirth/chonky_modernbert_base_1`, and `mirth/chonky_modernbert_large_1`. |
| `SlumberChunker` | `SlumberChunker(genie=None, tokenizer="character", chunk_size=2048, rules=None, candidate_size=128, min_characters_per_chunk=24, extract_mode="auto", max_retries=3, verbose=True)` | Genie/provider extra and credentials unless a custom offline/mock `BaseGenie` is supplied. | Default genie construction may require provider setup. `extract_mode` is `"text"`, `"json"`, or `"auto"`. |
| `TeraflopAIChunker` | `TeraflopAIChunker(client=None, url="https://api.segmentation.teraflopai.com/v1/segmentation/free", api_key=None, tokenizer="character")` | `teraflopai` extra and API key or provided client. | Uses `TERAFLOPAI_API_KEY` if `api_key` is absent. This sends input text to an external segmentation API. |

### Routing rule for optional chunkers

Use this sub-skill to explain constructor fields and safe fallbacks. Route model selection, embedding dimensions, provider API keys, caches, and live-service acceptance to `../embeddings-and-generative/`. Route CLI/API invocations of these chunkers to `../interfaces-and-deployment/`.

## Shared call surface

Most chunkers inherit:

```python
chunks = chunker.chunk(text)              # list[Chunk]
chunks = chunker(text)                    # same for a single string
batches = chunker.chunk_batch(list_texts) # list[list[Chunk]] for most chunkers
chunks = await chunker.achunk(text)       # async wrapper over chunk()
doc = chunker.chunk_document(document)    # fills document.chunks and propagates metadata
```

Notes:

- `TokenChunker.chunk_batch()` has a specialized signature: `chunk_batch(texts, batch_size=1, show_progress_bar=True)`.
- `FastChunker.chunk_batch(texts, show_progress=True)` ignores progress and returns fast per-text chunks.
- `chunk_document()` shallow-merges `Document.metadata` into each chunk's `metadata`; existing chunk keys win.
