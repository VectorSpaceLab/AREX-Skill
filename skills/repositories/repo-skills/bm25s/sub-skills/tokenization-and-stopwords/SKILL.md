---
name: tokenization-and-stopwords
description: "Tokenize bm25s documents and queries with consistent vocabularies,
  stopwords, stemming, streaming, and tokenizer persistence."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---
# Tokenization and stopwords

Use this route when the task is to turn text into bm25s token IDs or token strings, keep a corpus/query vocabulary aligned, configure stopwords or stemming, stream a large input, or persist tokenizer state. Keep BM25 indexing, retrieval, index-file persistence, and CLI search in their sibling routes.

## Choose the API first

- Use the module function `bm25s.tokenize` for a self-contained batch. It accepts one string or an iterable of strings and returns a `Tokenized` object by default.
- Use `bm25s.tokenization.Tokenizer` when corpus and query calls must share mutable vocabulary state, when a callable splitter is needed, or when streaming and vocab/stopword persistence are required.
- Do not confuse `return_ids` (module function) with `return_as` (class method). Details and signatures are in [references/api-reference.md](references/api-reference.md).

## Functional batch recipe

```python
import bm25s

corpus_tokens = bm25s.tokenize(
    ["A cat likes to purr", "A dog likes to play"],
    stopwords="en",
    show_progress=False,
)
assert hasattr(corpus_tokens, "ids") and hasattr(corpus_tokens, "vocab")
query_strings = bm25s.tokenize(
    "cat purr", stopwords="en", return_ids=False, show_progress=False
)
```

`return_ids=True` returns `Tokenized(ids=..., vocab=...)`; `return_ids=False` returns list-of-list strings. The module function builds a fresh vocabulary for each call, so IDs from separate calls are not a shared query vocabulary.

## Stateful corpus/query recipe

```python
from bm25s.tokenization import Tokenizer

tok = Tokenizer(
    lower=True,
    splitter=r"(?u)\\b\\w\\w+\\b",  # regex or callable
    stopwords="en",
    stemmer=None,
)
corpus_ids = tok.tokenize(
    ["A cat likes to purr", "A dog likes to play"],
    update_vocab=True,
    return_as="ids",
    show_progress=False,
)
query_ids = tok.tokenize(
    ["cat purr", "unknown term"],
    update_vocab=False,
    return_as="ids",
    show_progress=False,
)
query_text = tok.decode(query_ids)
```

Build the corpus vocabulary first. For ordinary retrieval queries, use `update_vocab=False` so unseen words are omitted rather than changing the indexed vocabulary. Use `update_vocab="never"` when even a known stem must not create a new surface-word mapping; this distinction matters with a stemmer.

## Operational rules

1. Text is lowercased first when `lower=True`, then split, stopword-filtered, and optionally stemmed. Custom stopword entries should normally already be lowercase.
2. IDs are assigned in first-seen order. With no stemmer, `get_vocab_dict()` is `word -> id`; with a stemmer it is `stem -> stem_id`.
3. The class defaults to English stopwords and `allow_empty=True`; its empty-token sentinel is deliberately documented in the API reference because empty behavior differs from the module function.
4. `Tokenizer.tokenize(..., update_vocab="if_empty")` updates only when `word_to_id` is empty. It is the class default. `streaming_tokenize` does not support this mode; choose `True`, `False`, or `"never"` there.
5. `return_as="stream"` is lazy and cannot be decoded until consumed. `length=` is needed when a non-streaming call receives a one-shot generator.
6. A callable class splitter receives one lowercased string and must return an iterable of strings. A class stemmer is called one word at a time. The module function instead calls a callable stemmer once with a list of unique tokens.
7. Persistence saves only tokenizer vocab dictionaries or stopwords. It does not save `lower`, splitter, stemmer, or other construction settings; recreate compatible settings before loading.

See [references/stemming-and-stopwords.md](references/stemming-and-stopwords.md) for language aliases and stemmer contracts, and [references/streaming-and-parallelism.md](references/streaming-and-parallelism.md) for lazy and multiprocessing patterns.

## Empty, unknown, and invalid inputs

- Keep `allow_empty` explicit in production recipes. At this revision, the module and class implement opposite-looking empty defaults: module `bm25s.tokenize(..., allow_empty=True)` leaves an empty document as `[]`, while `allow_empty=False` inserts `""`; the class inserts `""` for an empty document when `allow_empty=True` and has an existing/created sentinel, while `False` yields `[]`.
- With a stateful tokenizer and `update_vocab=False`, an unknown non-stemmed word is omitted. If no known IDs remain, the result is usually `[]`; an existing empty sentinel can make an empty class result `[empty_id]` when `allow_empty=True`.
- Unknown stopword names raise `ValueError`; pass `None`/`False` for no stopwords or pass a list.
- A non-callable class splitter/stemmer raises `ValueError` during construction. The module stemmer must expose `stemWords` or be callable on a token list; see the exact contracts in the references.

## Persist and reload safely

```python
from pathlib import Path

tok.save_vocab("tokenizer-state")
tok.save_stopwords("tokenizer-state")
# Recreate the same lower/splitter/stemmer configuration, then:
restored.load_vocab("tokenizer-state")
restored.load_stopwords("tokenizer-state")
```

Use the defaults `vocab.tokenizer.json` and `stopwords.tokenizer.json`, or explicit unique names. Never pass the BM25 index's `vocab.index.json` as `vocab_name`: `save_vocab` has no collision guard and can overwrite it. Run the bounded local check at [scripts/tokenizer_persistence_smoke.py](scripts/tokenizer_persistence_smoke.py) to verify a compatible state round trip without downloading a dataset.

## Handoff checklist

Before handing token IDs to a retrieval workflow, record the tokenizer settings, confirm corpus and query use the same `get_vocab_dict()`, and choose `allow_empty` deliberately. Prefer `Tokenized`/`to_tokenized_tuple` when the vocabulary must travel with IDs. Use [references/troubleshooting.md](references/troubleshooting.md) for failures involving optional PyStemmer, malformed callable outputs, one-shot streams, or persistence files.

Do not download BEIR/NQ data merely to validate tokenization. Use a tiny local fixture and `show_progress=False`; benchmark-scale multiprocessing is an opt-in adaptation described in the streaming reference.
