# Chunking and types troubleshooting

Use this reference to debug local Chonkie chunking before routing to pipeline, embedding/provider, CLI/API, or storage sub-skills.

## Fast triage

1. Confirm the task really belongs here:
   - Raw Python chunker APIs, tokenizers, offsets, and Chonkie dataclasses belong here.
   - Pipeline composition belongs in `../pipelines-and-processing/`.
   - Model/provider credentials, model cache, embeddings, genies, and neural devices belong in `../embeddings-and-generative/`.
   - CLI/API/server/cloud command construction belongs in `../interfaces-and-deployment/`.
   - Vector DB or file/dataset export belongs in `../integrations-and-storage/`.
2. Prefer deterministic fallback while debugging:

   ```python
   from chonkie import RecursiveChunker
   chunks = RecursiveChunker(tokenizer="character", chunk_size=512).chunk(text)
   ```

3. Run the bundled smoke with deterministic defaults:

   ```bash
   python scripts/chunking_smoke.py
   ```

## Import and optional dependency failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'chonkie'` | Chonkie is not installed in the active Python environment. | Install the package in the environment used to run the script or notebook. |
| Token, recursive, sentence imports work but model chunkers fail | Optional model extras were not installed. | Route to `../embeddings-and-generative/` and install only the selected extra, such as `chonkie[semantic]`, `chonkie[st]`, or `chonkie[neural]`. |
| `CodeChunker` import/initialization fails | `tree-sitter-language-pack` or grammar cache is missing. | Install `chonkie[code]`; for offline work, prepare/cache grammars before running `CodeChunker`. Use `RecursiveChunker` fallback if grammar setup is unavailable. |
| `SlumberChunker` fails on default construction | Default Genie/provider dependency or credentials are missing. | Supply a configured/mock `BaseGenie`, install the selected provider extra, or route provider setup to `../embeddings-and-generative/`. |
| `TeraflopAIChunker` raises an API-key error | No `api_key`, no `TERAFLOPAI_API_KEY`, and no preconfigured client. | Provide a client or key only when external API use is explicitly accepted. Otherwise use a local deterministic chunker. |
| Remote recipe loading fails in `from_recipe()` | Network/cache unavailable or recipe name/language invalid. | Use built-in `RecursiveRules()` or pass a local recipe path. |

## Chunks are too small

Common causes:

- `chunk_size` is too low.
- `chunk_overlap` is high, making useful new content per chunk smaller.
- `SentenceChunker` is forced to create chunks with `min_sentences_per_chunk` but each sentence is short.
- `RecursiveChunker` reaches a delimiter level that naturally yields small splits.
- `TableChunker` default row mode uses `chunk_size` as number of data rows, not model tokens.

Fixes:

```python
from chonkie import RecursiveChunker

chunker = RecursiveChunker(tokenizer="character", chunk_size=1024, min_characters_per_chunk=48)
chunks = chunker.chunk(text)
```

For retrieval overlap, add overlap later in a refinery/pipeline route instead of over-shrinking primary chunks here.

## Chunks are too large

Common causes:

- `chunk_size` is in tokenizer tokens, not characters, for most chunkers.
- `SentenceChunker` avoids splitting inside a long sentence.
- `RecursiveChunker` can keep large splits until it reaches deeper rule levels; custom rules may omit a token fallback.
- `FastChunker` uses byte limits, not tokenizer tokens.
- `CodeChunker` parser chunks can exceed the target by a small margin when preserving syntax structure.

Fixes:

- Need strict maximum size: use `TokenChunker`.
- Need better natural boundaries with eventual strict cap: first use `RecursiveChunker` with a token fallback level, then enforce hard caps with `TokenChunker` on oversized chunks.
- Need byte caps: use `FastChunker` and check encoded byte length.

```python
from chonkie import TokenChunker

chunks = TokenChunker(tokenizer="character", chunk_size=512).chunk(text)
assert all(c.token_count <= 512 for c in chunks)
```

## Offsets do not match source text

For deterministic text chunkers, validate offsets like this:

```python
for chunk in chunks:
    assert original[chunk.start_index:chunk.end_index] == chunk.text
```

If this fails:

- Make sure you are validating against the exact same string, including whitespace and line endings.
- Do not use whole-text reconstruction with overlapping `TokenChunker`; overlap duplicates text by design.
- For `TableChunker`, chunks intentionally repeat table headers. Validate row coverage or per-chunk offsets instead of joining chunk texts.
- For `CodeChunker`, validate ordered chunk text reconstruction first. If byte/character offsets diverge with non-ASCII code, prefer explicit `chunk.text` over slicing with assumptions.
- If chunking a `Document`, remember `chunk_document()` may re-chunk existing chunks and re-base indices.

## Token counts look wrong

Check the tokenizer:

```python
from chonkie import AutoTokenizer

tok = AutoTokenizer("character")
print(tok.count_tokens("hello"))  # 5
```

- `"character"` counts characters.
- `"word"` splits on literal spaces.
- `"byte"` counts UTF-8 bytes; non-ASCII characters can count as multiple bytes.
- `"row"` counts newline-separated rows and is mainly for `TableChunker`.
- `FastChunker` always sets `token_count` to `0` because it is byte-oriented.
- Callable-only tokenizers can count but cannot encode/decode; avoid them for chunkers that need token windows.

## `TokenChunker` problems

| Problem | Fix |
| --- | --- |
| `chunk_overlap must be less than chunk_size` | Use an overlap integer smaller than `chunk_size`, or a float fraction less than `1.0`. |
| Empty output | Input is empty or whitespace-only. |
| Joined chunk texts duplicate content | You used overlap; validate coverage differently. |
| Custom tokenizer fails in `decode_batch` | Use a tokenizer object with encode/decode/batch methods, not a callable-only counter. |

## `SentenceChunker` problems

| Problem | Fix |
| --- | --- |
| One giant chunk | Input has too few delimiters, delimiters do not match punctuation spacing, or `chunk_size` is large. Adjust `delim` and `min_characters_per_sentence`. |
| Unexpected punctuation placement | Set `include_delim="prev"`, `"next"`, or `None` explicitly. |
| Value errors on minima | `chunk_size > 0`, `chunk_overlap < chunk_size`, `min_sentences_per_chunk >= 1`, and `min_characters_per_sentence >= 1` are required. |
| Deprecation warning for `approximate` | Leave `approximate=False`; exact token counting is the current path. |

## `RecursiveChunker` problems

| Problem | Fix |
| --- | --- |
| Custom rules rejected | A `RecursiveLevel` can use only one splitting method: `delimiters`, `whitespace=True`, or `pattern`. |
| Whitespace delimiter rejected | Use `RecursiveLevel(whitespace=True)` instead of `delimiters=[" "]`. |
| Oversized chunks remain | Include deeper fallback levels, especially `RecursiveLevel(whitespace=True)` and final `RecursiveLevel()`. |
| Offline recipe failure | Use `RecursiveRules()` defaults or a local recipe `path`. |

## `TableChunker` problems

- Markdown tables must include a header, separator line, and at least one data row.
- Row mode repeats the header in every chunk and counts only data rows as `token_count`.
- Tokenizer mode includes header/footer token counts; very large headers can dominate a small `chunk_size`.
- For raw markdown documents, table extraction is a pipeline/chef concern. Route extraction to `../pipelines-and-processing/`, then use `TableChunker` on extracted table strings or `MarkdownDocument.tables`.

Minimal valid markdown table:

```python
table = "| item | qty |\n|---|---|\n| tea | 2 |\n"
```

## `CodeChunker` problems

- Install the `code` extra before using `CodeChunker`.
- Specify `language="python"` or another known language instead of `"auto"` when possible.
- Invalid syntax may reduce parse quality; fall back to `RecursiveChunker` when AST parsing is unavailable.
- The dependency can initialize/download language grammars. For deterministic/offline tasks, probe grammar availability first. The bundled smoke only runs code chunking when it can avoid implicit grammar downloads unless you explicitly allow them.
- For markdown code blocks, prefer `MarkdownDocument` with `MarkdownCode` entries so offsets can be re-based into the source markdown.

## Optional model/provider chunker problems

| Chunker | Common issue | Deterministic fallback |
| --- | --- | --- |
| `SemanticChunker` | Missing embeddings extra, model cache, or provider key; invalid threshold/filter parameters. | `RecursiveChunker` or `SentenceChunker`; route model setup to `../embeddings-and-generative/`. |
| `LateChunker` | Missing `sentence-transformers`/`st` extra or model download. | `RecursiveChunker` with the same `RecursiveRules`. |
| `NeuralChunker` | Missing transformers/torch, unsupported model name, failed model/tokenizer download, device-map issue. | `RecursiveChunker`; route device/model plan to `../embeddings-and-generative/`. |
| `SlumberChunker` | Missing genie/provider dependencies, credentials, or JSON extraction support. | `RecursiveChunker`; if semantic quality is required, route provider setup to `../embeddings-and-generative/`. |
| `TeraflopAIChunker` | Missing `teraflopai` package or API key; external API use not accepted. | Local `RecursiveChunker`/`TokenChunker`. |

## When to escalate

Escalate out of this sub-skill when the fix requires:

- Installing or selecting embedding models, neural models, genies, or provider credentials: `../embeddings-and-generative/`.
- Building a multi-step processing pipeline or extracting tables/code from files: `../pipelines-and-processing/`.
- Generating or debugging CLI/API calls: `../interfaces-and-deployment/`.
- Writing chunks into JSON, datasets, or vector databases: `../integrations-and-storage/`.
