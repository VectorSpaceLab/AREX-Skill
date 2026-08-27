# Tokenization troubleshooting

## Install and import

**`ModuleNotFoundError: No module named 'bm25s'`**

Install the package in the active environment (`pip install bm25s`) or install the local project in editable mode from the project owner’s chosen checkout. Confirm the interpreter and package agree with `python -c "import bm25s; print(bm25s.__file__)"`. Do not mix a shell's `python` with a different environment's `pip`.

The base package requires NumPy. Importing `bm25s.tokenization` also imports the package initializer, so an unrelated optional backend import failure can appear before tokenization code; diagnose the environment's package set rather than changing tokenizer arguments.

**Progress output or missing tqdm**

`tqdm` is optional. Install it if progress bars are wanted, or consistently pass `show_progress=False` (and `leave=False`) in tests, workers, services, and scripts. The tokenizer has a fallback iterator when tqdm is absent.

## Optional stemmers and stopwords

**`Stemmer` cannot be imported**

PyStemmer is optional. Omit `stemmer` for unstemmed IDs, install the package's stem extra, or provide a tested adapter. Do not silently substitute a batch stemmer for the class's per-word contract.

**`stemmer must be callable...` / `Stemmer must have...`**

For `Tokenizer`, pass `None`, a callable `word: str -> str`, or an object with `stemWord`. For module `bm25s.tokenize`, pass `None`, a callable `list[str] -> list[str]`, or an object with `stemWords`. An NLTK single-word stemmer needs a list adapter such as `lambda words: [porter.stem(word) for word in words]`.

**Unknown stopword name**

Only the aliases in [stemming-and-stopwords.md](stemming-and-stopwords.md) are recognized. Use a custom lowercase list for another language/domain, or use `stopwords=None`/`False` to disable filtering. A language code is not a remote lookup and does not trigger a download.

## Data and configuration

**Too many or too few tokens**

Check, in order: `lower`, regex/callable splitter, stopword spelling/case, stemmer adapter shape, and `allow_empty`. The default regex requires at least two word characters; use `r"\w+"` or a callable splitter when one-character tokens are required. A callable class splitter receives the already-lowercased full string and must return strings, not IDs.

**Custom splitter fails or emits odd IDs**

A non-callable splitter is rejected at construction. A callable returning `None`, nested lists, integers, or a generator that is consumed unexpectedly violates the implicit contract. Validate it independently:

```python
splitter = lambda text: text.split()
assert splitter("A B") == ["A", "B"]
```

Use `show_progress=False` while isolating splitter behavior.

**Corpus and query IDs do not match**

The module function creates a fresh vocabulary on every call. For shared IDs, use one `Tokenizer`, tokenize the corpus with `update_vocab=True` (or the first `"if_empty"` call), and tokenize queries with `False` or `"never"`. Keep the same stemmer, splitter, stopwords, `lower`, and `allow_empty` settings. Prefer `Tokenized`/`to_tokenized_tuple` when passing vocab with IDs.

**Unknown-only query is empty**

This is expected with a frozen unstemmed vocabulary: unknown words are omitted. If an empty sentinel is already present and the class uses `allow_empty=True`, a no-token document can instead contain that sentinel. Decide whether zero-token queries should be handled by the retrieval layer or rejected before it.

## API and CLI boundaries

**`ValueError` for `return_as` or `update_vocab`**

The class accepts only `return_as` in `ids`, `string`, `tuple`, `stream`, and `update_vocab` in `True`, `False`, `"if_empty"`, `"never"`. The module function has no `return_as`; use `return_ids=True/False`.

**`TypeError: object has no len()` on a generator**

Pass `length=` for an eager `Tokenizer.tokenize` call over a one-shot iterable, or use `return_as="stream"` and consume the generator. The module function accepts an iterable without a length parameter.

**Trying to configure tokenization through `bm25` CLI**

The tokenizer class has no separate tokenizer CLI. The high-level/CLI route owns file loading and its internal defaults. For custom splitter, stateful vocab, stemming adapters, or streaming, use the Python APIs in this skill and route file-search/CLI questions to the high-level skill.

## Persistence and workflow failures

**Reloaded IDs differ**

`save_vocab` stores the three vocabulary dictionaries only. Recreate the same `lower`, splitter, and stemmer behavior before `load_vocab`; then use `update_vocab=False`/`"never"`. A different stemmer or regex changes which strings map to IDs even when the JSON file is intact.

**Stopwords did not survive reload**

Call `save_stopwords` and `load_stopwords` separately. `load_vocab` does not load stopwords, and `load_stopwords` does not load vocabulary. A loaded stopword file is decoded as a JSON list even if the original built-in value was a tuple; compare by sequence contents.

**Index files disappeared after saving tokenizer state**

The tokenizer saver does not prevent filename collisions. Never set `vocab_name="vocab.index.json"`; use `vocab.tokenizer.json` or another tokenizer-specific name. Keep tokenizer state and BM25 index files in a directory only when every filename is distinct.

**Persistence smoke check fails in a read-only directory**

Use a caller-owned writable directory or a temporary directory. Save methods create missing directories; load methods require the exact file and filename to already exist. The bounded check is [../scripts/tokenizer_persistence_smoke.py](../scripts/tokenizer_persistence_smoke.py).

**Parallel output differs from sequential output**

Independent worker IDs are not globally meaningful. Compare worker results as strings, preserve chunk order, disable progress in workers, and ensure the splitter/stemmer adapter is serializable. If IDs are required, distribute a previously loaded canonical vocab and freeze updates.
