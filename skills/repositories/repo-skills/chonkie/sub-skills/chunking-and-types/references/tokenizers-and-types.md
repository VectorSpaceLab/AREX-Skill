# Tokenizers and type contracts

Use this reference when Chonkie chunk behavior depends on token counting, offsets, metadata propagation, or data object serialization.

## Tokenizer loading

Chonkie chunkers accept either a tokenizer string or an object implementing the tokenizer protocol. Internally, `AutoTokenizer(...)` wraps the input and exposes a common interface.

```python
from chonkie import AutoTokenizer

tok = AutoTokenizer("character")
ids = tok.encode("abc")
text = tok.decode(ids)
count = tok.count_tokens("abc")
```

### Built-in tokenizer strings

| String | Underlying tokenizer | Count meaning | Best use | Caution |
| --- | --- | --- | --- | --- |
| `"character"` | `CharacterTokenizer` | Unicode code points / Python characters | Deterministic smokes, small examples, offset-debugging | Counts characters, not model tokens. |
| `"word"` | `WordTokenizer` | `text.split(" ")` pieces | Rough word budgets | Multiple spaces and empty strings follow Python split behavior. |
| `"byte"` | `ByteTokenizer` | UTF-8 bytes | Byte-sensitive payloads, non-ASCII size checks | Token count differs from character count for Unicode. |
| `"row"` | `RowTokenizer` | Newline-separated rows | `TableChunker` row budgets | Empty text counts as `0`; non-empty text counts line breaks. |

Other strings such as tokenizer/model identifiers are delegated through installed tokenizer backends. They may need model/tokenizer cache availability. For fully offline deterministic chunking, prefer built-in strings.

### Accepted tokenizer objects

`AutoTokenizer` accepts:

- Another `AutoTokenizer` instance (returned as-is).
- A Chonkie `Tokenizer` instance such as `CharacterTokenizer()`, `WordTokenizer()`, `ByteTokenizer()`, or `RowTokenizer()`.
- Tokie tokenizer objects.
- Hugging Face `transformers` tokenizers.
- Hugging Face `tokenizers` tokenizers.
- `tiktoken` encodings.
- A callable token counter, with important limits.

A custom object should implement:

```python
class TokenizerProtocol:
    def encode(self, text: str): ...
    def decode(self, tokens): ...
    def tokenize(self, text: str): ...
```

If you pass a callable, Chonkie can count tokens with `count_tokens`, but `encode`, `decode`, `encode_batch`, and `decode_batch` are not implemented. Do not use callable-only tokenizers with chunkers that need to encode and decode token windows, such as `TokenChunker` or the token fallback level of `RecursiveChunker`.

## Tokenizer methods

| Method | Contract |
| --- | --- |
| `encode(text)` | Return a sequence of integer token ids. |
| `decode(tokens)` | Convert token ids back to text. |
| `tokenize(text)` | Return token pieces or ids, depending on backend. |
| `count_tokens(text)` | Return an integer count; falls back to `len(encode(text))` when no native count is available. |
| `encode_batch(texts)` | Batch version of `encode`; not available for callable-only tokenizers. |
| `decode_batch(token_sequences)` | Batch version of `decode`; not available for callable-only tokenizers. |
| `count_tokens_batch(texts)` | Batch version of `count_tokens`; may fall back to per-text counts. |

## Core `Chunk` contract

```python
from chonkie import Chunk

chunk = Chunk(
    text="example",
    start_index=0,
    end_index=7,
    token_count=7,
    context=None,
    embedding=None,
    metadata={"source": "inline"},
)
```

Fields:

| Field | Meaning |
| --- | --- |
| `id` | Auto-generated id with a `chnk_` prefix unless supplied. |
| `text` | Chunk text. `str(chunk)` returns this text; iterating a chunk iterates the text. |
| `start_index` / `end_index` | Character offsets into the source string for normal text chunkers. `FastChunker` converts byte offsets back to character positions. `CodeChunker` offsets are parser byte-derived but are re-based so reconstruction tests should still use returned `chunk.text` order. |
| `token_count` | Count according to the chunker's tokenizer. `FastChunker` sets this to `0` intentionally. |
| `context` | Optional context string; not automatically populated by basic chunkers. |
| `embedding` | Optional vector as a list or numpy array. Model-dependent chunkers/refineries can populate it. |
| `metadata` | Arbitrary dictionary. `BaseChunker.chunk_document()` merges parent `Document.metadata` into each chunk; chunk keys take precedence. |

Useful methods:

```python
as_dict = chunk.to_dict()        # numpy embeddings become lists
clone = chunk.copy()             # deep copy through dict round-trip
restored = Chunk.from_dict(as_dict)
```

## `Sentence` contract

`Sentence` objects are internal/useful when debugging sentence or semantic chunking. They validate values on construction.

```python
from chonkie import Sentence

sentence = Sentence(text="Hello.", start_index=0, end_index=6, token_count=1)
```

Validation rules:

- `text` must be a string.
- `start_index` and `end_index` must be non-negative integers.
- `start_index <= end_index` is allowed; equal indices are valid.
- `token_count` must be non-negative.
- `embedding` may be absent, a list, or a numpy array; `to_dict()` serializes numpy arrays to lists.

## `Document` and markdown contracts

```python
from chonkie import Document, MarkdownDocument, MarkdownTable, MarkdownCode, MarkdownImage

doc = Document(content="text", metadata={"file": "example.md"})
```

| Type | Fields | Usage |
| --- | --- | --- |
| `Document` | `id`, `content`, `chunks`, `metadata` | Generic text/document container. `chunk_document()` fills or re-chunks `chunks`. |
| `MarkdownDocument` | all `Document` fields plus `tables`, `code`, `images` | Markdown-aware container for table/code/image positions. |
| `MarkdownTable` | `content`, `start_index`, `end_index` | Table string plus offsets into markdown. Used by `TableChunker.chunk_document()`. |
| `MarkdownCode` | `content`, optional `language`, `start_index`, `end_index` | Fenced/code block content and language hint. Used by `CodeChunker.chunk_document()`. |
| `MarkdownImage` | `alias`, `content`, `start_index`, `end_index`, optional `link` | Image metadata; not chunked by this sub-skill. |

Example: chunk markdown tables already extracted into a `MarkdownDocument`:

```python
from chonkie import MarkdownDocument, MarkdownTable, TableChunker

markdown = "Intro\n\n| item | qty |\n|---|---|\n| tea | 2 |\n| rice | 1 |\n"
start = markdown.index("| item")
table = MarkdownTable(content=markdown[start:], start_index=start, end_index=len(markdown))
doc = MarkdownDocument(content=markdown, tables=[table], metadata={"kind": "inventory"})
result = TableChunker(chunk_size=1).chunk_document(doc)
assert result.chunks[0].metadata["kind"] == "inventory"
```

## Recursive rules

`RecursiveChunker` is controlled by `RecursiveRules`, a list of `RecursiveLevel` objects. A level can use exactly one splitting method.

```python
from chonkie import RecursiveLevel, RecursiveRules

rules = RecursiveRules(levels=[
    RecursiveLevel(delimiters=["\n\n", "\n"], include_delim="prev"),
    RecursiveLevel(delimiters=[". ", "! ", "? "], include_delim="prev"),
    RecursiveLevel(whitespace=True),
    RecursiveLevel(),  # token-window fallback
])
```

`RecursiveLevel` fields:

| Field | Contract |
| --- | --- |
| `delimiters` | String or list of non-empty delimiter strings. Do not use whitespace-only delimiters; set `whitespace=True` instead. |
| `whitespace` | Boolean flag to split on spaces. Mutually exclusive with `delimiters` and `pattern`. |
| `include_delim` | `"prev"`, `"next"`, or `None`; controls which side receives delimiters. |
| `pattern` | Optional non-empty regex pattern. It is validated, but core chunker behavior should be tested before relying on pattern-heavy rules. |
| `pattern_mode` | `"split"` or `"extract"`. |

Default `RecursiveRules()` creates five levels: paragraph breaks, sentence delimiters, punctuation/pauses, whitespace, and token fallback.

Serialization:

```python
payload = rules.to_dict()
restored = RecursiveRules.from_dict(payload)
```

Recipe loading:

```python
rules = RecursiveRules.from_recipe(name="default", lang="en", path=None)
```

For offline or reproducible workflows, supply a local `path` to the recipe rather than relying on remote recipe lookup.

## Code rule dataclasses

These are configuration/data objects for code chunking rules and language metadata:

```python
from chonkie import MergeRule, SplitRule, LanguageConfig
```

| Type | Fields | Notes |
| --- | --- | --- |
| `MergeRule` | `name`, `node_types`, optional `text_pattern`, `bidirectional=False` | Describes adjacent AST node merging. |
| `SplitRule` | `name`, `node_type`, `body_child`, optional `exclude_nodes`, `recursive=False` | Describes splitting large AST nodes by body child. |
| `LanguageConfig` | `language`, `merge_rules`, `split_rules` | Groups code rules for a language. |

Most users configure `CodeChunker(language=..., chunk_size=...)` directly and do not need to create these dataclasses.

## Offset and reconstruction checks

Use these checks when debugging a deterministic chunker:

```python
def assert_offsets(chunks, original):
    for chunk in chunks:
        assert 0 <= chunk.start_index <= chunk.end_index <= len(original)
        assert original[chunk.start_index:chunk.end_index] == chunk.text
```

Caveats:

- `TokenChunker` with overlap intentionally duplicates content across chunks; do not assert `"".join(c.text for c in chunks) == original` when overlap is non-zero.
- `FastChunker` is byte-sized and reports `token_count == 0`; check `len(chunk.text.encode("utf-8"))` rather than `token_count`.
- `TableChunker` chunks include repeated headers; reconstruct data rows, not whole chunk text, if validating table preservation.
- Model-dependent chunkers may attach embeddings; serialize with `to_dict()` before JSON export.
