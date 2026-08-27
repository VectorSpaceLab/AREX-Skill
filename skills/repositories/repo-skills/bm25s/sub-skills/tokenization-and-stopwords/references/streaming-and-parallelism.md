# Streaming and parallelism

## Lazy class tokenization

`Tokenizer.streaming_tokenize` yields one `list[int]` per input document and mutates the tokenizer vocabulary as the generator is consumed when `update_vocab=True`.

```python
from bm25s.tokenization import Tokenizer

tok = Tokenizer(stopwords=None)
stream = tok.streaming_tokenize(
    (text for text in ["alpha beta", "beta gamma"]),
    update_vocab=True,
    allow_empty=False,
)
for doc_ids in stream:
    consume(doc_ids)  # vocab grows in first-seen order
```

The return value is a generator, so construction alone does not tokenize input or finish vocabulary updates. Exceptions from a splitter/stemmer and missing input values appear during iteration. A generator can be consumed only once.

Supported practical `streaming_tokenize` update values are `True`, `False`, and `"never"`:

- `True` adds new unstemmed words or stems.
- `False` emits known words; with a stemmer it may map a new surface form to a stem ID already in `stem_to_sid`. The class can still cache that surface-to-stem calculation in `word_to_stem`.
- `"never"` emits already known surface IDs but does not add a new surface mapping, even when its stem is known; it can still populate the `word_to_stem` cache while inspecting an unseen word.

Use `Tokenizer.tokenize(..., return_as="stream")` when the same lazy generator return mode is desired through the main class API. `return_as="stream"` bypasses eager collection and progress-bar iteration. `streaming_tokenize` itself does not implement `"if_empty"`; `Tokenizer.tokenize` resolves that mode against the current vocabulary before calling it.

## Eager class calls over one-shot iterables

For `return_as="ids"`, `"string"`, or `"tuple"`, `Tokenizer.tokenize` eventually calls `len(texts)` when `length` is omitted. A list is fine; a generator is not:

```python
texts = (line for line in ["alpha beta", "gamma delta"])
ids = tok.tokenize(
    texts,
    length=2,
    update_vocab=True,
    return_as="ids",
    show_progress=False,
)
```

Set `show_progress=False` in libraries, tests, workers, and non-interactive runs. `leave_progress` only controls whether an enabled tqdm bar remains after completion. The module function has its own `show_progress`/`leave` names and has no `length` argument.

## Shared vocabulary for queries

A stream is useful for a large query set only after the corpus vocabulary is fixed:

```python
corpus_ids = tok.tokenize(corpus, update_vocab=True, show_progress=False)
query_stream = tok.tokenize(
    queries,
    update_vocab=False,
    return_as="stream",
    show_progress=False,
)
for query_ids in query_stream:
    # query_ids use tok.get_vocab_dict(); unknown words are omitted
    handle(query_ids)
```

If the vocabulary must be frozen even for known stems represented by a new surface form, use `update_vocab="never"`. Keep `lower`, splitter, stopwords, stemmer, and `allow_empty` identical between corpus and queries. Use `to_tokenized_tuple` after collecting IDs if the downstream consumer needs IDs and the shared vocab together.

## Empty documents in a stream

The class's `allow_empty=True` path can create an empty-string sentinel ID when updating a fresh vocabulary. A no-token document can then yield `[empty_id]`. With `allow_empty=False`, an empty split yields `[]`. This is the class behavior; the module function has the opposite branch behavior documented in [api-reference.md](api-reference.md). Choose and test one policy before indexing.

## Safe multiprocessing adaptation

There is no built-in parallel `Tokenizer` vocabulary coordinator. The safe pattern for independent text conversion is to process chunks with the **module** function and return strings:

```python
# worker module scope
import bm25s

def tokenize_chunk(texts):
    return bm25s.tokenize(
        texts, return_ids=False, stopwords="en", show_progress=False
    )
```

Map `tokenize_chunk` over chunks with a process pool and flatten results in input order. This avoids pretending that each worker's independently created integer IDs share one vocabulary. The returned strings can be centrally tokenized later, or can be compared with a sequential string result.

Do not share one mutable `Tokenizer` instance between processes. Its three vocabulary dictionaries are process-local and concurrent updates cannot establish a deterministic global first-seen order. A C-backed stemmer object may also be unpicklable. If workers must emit IDs, first establish a canonical vocabulary in one process, persist it with `save_vocab`, have each worker construct the same tokenizer configuration and `load_vocab`, then tokenize with `update_vocab="never"` or `False`; explicitly decide whether unknown tokens should be dropped.

Multiprocessing has process-start, memory, and serialization costs. Use it only after measuring a local fixture. Do not copy a benchmark or dataset downloader into a normal tokenization workflow.

## Memory and correctness checks

- Prefer a class stream when one shared vocabulary and bounded per-document memory matter.
- Consume and persist a vocabulary only after the corpus stream is complete; stopping early leaves partial state.
- If a downstream operation needs all IDs, collect the generator once and check its length against the input count.
- For parallel strings, assert flattened output order and count; for parallel IDs, assert every worker loaded the same vocab before processing.
