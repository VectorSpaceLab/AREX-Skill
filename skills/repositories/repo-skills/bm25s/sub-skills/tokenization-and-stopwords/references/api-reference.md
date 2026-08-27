# Tokenization API reference

This reference records the public behavior of the `ce881e1` package revision represented by this skill. Examples suppress progress output so their return values are inspectable.

## `bm25s.tokenize`

The package re-exports `bm25s.tokenization.tokenize` as `bm25s.tokenize`.

```python
bm25s.tokenize(
    texts,
    lower=True,
    token_pattern=r"(?u)\b\w\w+\b",
    stopwords="english",
    stemmer=None,
    return_ids=True,
    show_progress=True,
    leave=False,
    allow_empty=True,
)
```

- `texts`: one `str` or a collection/iterable of strings. A single string is wrapped as a one-document list. A `Tokenizer` instance does **not** provide that wrapping convenience; pass it a list.
- `lower`: lowercase before regex splitting.
- `token_pattern`: regex string compiled and used with `findall`; it is not a callable parameter.
- `stopwords`: supported language name/code, a list, `None`, or `False`. Defaults to English. The complete alias table is in [stemming-and-stopwords.md](stemming-and-stopwords.md).
- `stemmer`: an object with `stemWords(list[str]) -> list[str]`, or a callable with that same batch contract.
- `return_ids=True`: return `Tokenized(ids, vocab)`. `vocab` is token/stem string to integer ID.
- `return_ids=False`: return `list[list[str]]`; no vocabulary is returned.
- `show_progress` and `leave`: control the split, stem, and reconstruction progress bars.
- `allow_empty`: see the version-specific behavior below.

### Functional output example

```python
import bm25s

ids_and_vocab = bm25s.tokenize(
    ["A cat and a dog"], stopwords=None, show_progress=False
)
assert ids_and_vocab.ids == [[0, 1, 2]]
assert ids_and_vocab.vocab == {"cat": 0, "and": 1, "dog": 2}
```

The illustrative IDs above assume the default two-character regex and first-seen assignment; use the returned `vocab` rather than hard-coding IDs. `Tokenized` is a `NamedTuple` with fields `ids` and `vocab`, so it supports both `result.ids` and tuple destructuring.

## `Tokenized` and conversion

```python
from bm25s.tokenization import Tokenized, convert_tokenized_to_string_list

Tokenized(ids: list[list[int]], vocab: dict[str, int])
strings = convert_tokenized_to_string_list(tokenized)
```

`convert_tokenized_to_string_list` reverses the supplied vocabulary and converts each ID. `Tokenizer.to_tokenized_tuple(docs)` does the same kind of packaging using that tokenizer's current vocabulary. `Tokenizer.decode(docs)` reverses IDs using `get_vocab_dict()` at decode time. IDs absent from the reverse mapping raise `KeyError`; do not decode IDs with a different vocabulary.

## `Tokenizer` constructor

```python
Tokenizer(
    lower=True,
    splitter=r"(?u)\b\w\w+\b",
    stopwords="english",
    stemmer=None,
)
```

- A string `splitter` is compiled as a regex and called with `findall`.
- A callable `splitter` receives the lowercased document and must return an iterable of string tokens. `lambda text: text.split()` is a simple whitespace splitter.
- A non-callable splitter raises `ValueError("splitter must be a callable or a regex pattern.")`.
- An object with `stemWord` is adapted to that bound method. Otherwise a callable stemmer is called for each token. A non-callable, non-`None` value raises `ValueError`.
- `stopwords` is normalized immediately by `_infer_stopwords`; unknown string names raise `ValueError`.
- Construction starts with empty `word_to_stem`, `stem_to_sid`, and `word_to_id` dictionaries.

## `Tokenizer.tokenize`

```python
tok.tokenize(
    texts,
    update_vocab="if_empty",
    leave_progress=False,
    show_progress=True,
    length=None,
    return_as="ids",
    allow_empty=True,
)
```

`update_vocab` must be `True`, `False`, `"if_empty"`, or `"never"`; any other value raises `ValueError`. `"if_empty"` is converted to `True` only when `word_to_id` is empty, otherwise to `False`.

| `return_as` | Return value | Typical use |
|---|---|---|
| `"ids"` | `list[list[int]]` | BM25 corpus/query IDs |
| `"string"` | `list[list[str]]` | inspect/decode token strings |
| `"tuple"` | `Tokenized` | carry IDs and current vocab together |
| `"stream"` | generator of `list[int]` | consume one document at a time |

Invalid `return_as` raises `ValueError`. `length` is used only for the eager progress total; it is important when `texts` is a generator and an eager return mode is selected. `return_as="stream"` returns immediately and does not require `length`.

### Vocabulary update modes

Without a stemmer:

- `True`: add every non-stopword token, assigning the next integer ID.
- `False`: emit only words already in `word_to_id`; do not add unknown words.
- `"if_empty"`: first-call behavior (`True` if empty), then behaves as `False` until `reset_vocab()`.
- `"never"`: emit existing words but never add a word.

With a stemmer, `stem_to_sid` is the retrieval vocabulary. Existing surface words in `word_to_id` are emitted first. A new surface word whose stem is already known can be mapped under `False`; `"never"` suppresses that mapping too. The implementation may still cache an unseen surface-to-stem result in `word_to_stem` under `False`/`"never"`; that cache is not an emitted vocabulary ID. New stems are not emitted unless vocabulary updating is `True`.

## Streaming and state methods

```python
tok.streaming_tokenize(texts, update_vocab=True, allow_empty=True)
tok.get_vocab_dict()
tok.reset_vocab()
tok.to_tokenized_tuple(docs)
tok.decode(docs)
```

`streaming_tokenize` is a generator. Its documented update values are `True`, `False`, and `"never"`; `"if_empty"` is intentionally handled by `tokenize`, not this method. `get_vocab_dict()` returns `word_to_id` without stemming and `stem_to_sid` with stemming. `reset_vocab()` clears all three internal dictionaries, not stopwords or tokenizer configuration.

## Persistence methods

```python
tok.save_vocab(save_dir, vocab_name="vocab.tokenizer.json")
tok.load_vocab(save_dir, vocab_name="vocab.tokenizer.json")
tok.save_stopwords(save_dir, stopwords_name="stopwords.tokenizer.json")
tok.load_stopwords(save_dir, stopwords_name="stopwords.tokenizer.json")
```

Saving creates `save_dir`; loading does not. Vocab JSON contains `word_to_stem`, `stem_to_sid`, and `word_to_id`. Stopword JSON contains the current stopword sequence. Neither file stores lowercasing, splitter, stemmer, or update policy. Keep `vocab.tokenizer.json` distinct from an index's `vocab.index.json`; the tokenizer saver does not protect a caller from an explicitly colliding filename.

## Empty-token behavior at this revision

The parameter documentation and implementation branches are not symmetric between APIs. Test this choice instead of assuming a generic convention:

| Call | Empty document result on a fresh instance |
|---|---|
| `bm25s.tokenize([""], allow_empty=True)` | `[[]]`, vocab remains empty |
| `bm25s.tokenize([""], allow_empty=False)` | `[[0]]`, vocab contains `{"": 0}` |
| `Tokenizer().tokenize([""], allow_empty=True)` | `[[0]]`, class creates/uses `""` sentinel when updating |
| `Tokenizer().tokenize([""], allow_empty=False)` | `[[]]` |

For the class, an existing empty sentinel may be emitted for a no-token document even with `update_vocab=False` and `allow_empty=True`. This is why corpus and query calls must agree on `allow_empty` and why an index workflow must make its empty-token policy explicit.
