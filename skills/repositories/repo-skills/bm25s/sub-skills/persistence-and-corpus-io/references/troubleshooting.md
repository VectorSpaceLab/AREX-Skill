# Persistence and corpus troubleshooting

Diagnose the artifact and the exact load arguments before changing parameters.
Do not silence warnings or enable pickle as a generic repair.

## Install and import

- **`ModuleNotFoundError: bm25s`** — install the package in the active Python
  environment (`python -m pip install bm25s`) or install the checked-out
  package for development. Confirm `python -c "import bm25s; print(bm25s.__version__)"`
  uses the same interpreter that runs the application.
- **`orjson` is absent** — local JSON persistence falls back to the Python
  standard-library encoder/decoder. Install `bm25s[core]` only when the
  application wants the optional faster JSON/progress/stemming/Numba bundle;
  absence of `orjson` is not an index corruption error.
- **Progress import errors** — `tqdm` is optional and progress bars can be
  disabled with `show_progress=False`. A CPU NumPy persistence workflow does
  not require CUDA or a GPU.
- **Tokenizer or stemmer import errors during a text-query reload** — restore
  the tokenizer with the same preprocessing dependencies, or use already
  aligned integer token IDs. Loading the BM25 arrays alone cannot reconstruct a
  missing tokenizer or stemmer.

## Missing or corrupt files

- **`FileNotFoundError` for `params.index.json`** — the directory is not a
  complete BM25 save or `params_name` is wrong. Locate the matching metadata;
  do not create an empty JSON file.
- **Missing data/indices/indptr** — check every custom array name passed to
  `load` and ensure the files came from the same save. A directory containing
  only the corpus or vocabulary is not a usable index.
- **Missing `vocab.index.json`** — pass `load_vocab=False` only for array or
  metadata inspection. In this version the loaded `vocab_dict` and
  `unique_token_ids_set` are empty, so normal retrieval still requires the
  saved BM25 vocabulary.
- **Malformed JSON or NumPy load errors** — treat truncation, a partial copy,
  wrong encoding, or a mixed-version directory as an artifact problem. Restore
  the complete directory and retry with `allow_pickle=False` first.
- **`FileNotFoundError: Non-occurrence array not found`** — a BM25L or BM25+
  index is incomplete, or `nnoc_name` does not match the save. Restore that
  array; do not relabel the method to bypass the check because scores would be
  wrong.
- **Custom filenames load successfully for arrays but not in `bm25 search`**
  — the CLI calls the default `BM25.load` names. Use default filenames for
  the CLI's local index layout, or call `BM25.load` yourself with every custom
  name. CLI/high-level input parsing is a separate route.

## Corpus and JSONL problems

- **No corpus after `load_corpus=True`** — the named corpus file is absent;
  the low-level loader intentionally returns the index without raising. Check
  `retriever.corpus is not None` before requesting documents.
- **`IndexError`, wrong documents, or plausible but shifted results** — compare
  `len(retriever.corpus)` with `retriever.scores["num_docs"]` and verify order,
  not just IDs. Recreate the corpus from the same snapshot used to index it.
- **JSONL line fails to decode** — inspect the exact line for a blank/truncated
  record or unsupported value. Saved JSONL is UTF-8 and has one JSON value per
  line; remove malformed lines only if rebuilding the index/corpus alignment is
  acceptable.
- **`JsonlCorpus` returns wrong lines or decoding fails after file replacement**
  — its `.mmindex.json` companion is stale. Delete the companion and construct
  the reader again so offsets are rescanned. Do not edit only the companion to
  conceal a changed corpus.
- **A document disappeared during save** — save logs a warning and skips a
  document if JSON encoding fails. Check the number of JSONL lines and replace
  custom objects, bytes, sets, or NumPy values with plain JSON-compatible
  values before saving.
- **Empty JSONL with `mmap=True`** — an empty file cannot be memory-mapped on
  common Python platforms. Use `mmap=False` or keep an empty corpus out of the
  `JsonlCorpus` path.
- **Access after `JsonlCorpus.close()`** — call `corpus.load()` before indexing
  into it again. Close readers during cleanup to release file descriptors and
  mapped pages.

## API and configuration mistakes

- **`ValueError: `mmap` must be a boolean`** — pass exactly `True` or `False` to
  `BM25.load`; do not pass strings such as `"true"`.
- **Text or integer query fails after `load_vocab=False`** — load the saved
  BM25 vocabulary (`load_vocab=True`) and preserve matching preprocessing. A
  separately tokenized vocabulary with different token IDs is not compatible
  merely because the words match.
- **`load_scores` object cannot retrieve** — `load_scores` is intentionally
  partial. It does not load model method, `k1`, `b`, vocabulary, or the
  BM25L/BM25+ correction. Use `BM25.load` for retrieval; if using
  `load_scores` in a controlled batch loop, retain the fully loaded object and
  pass the saved `num_docs`.
- **`k` exceeds the corpus/index size** — reduce `k` or repair the corpus/index
  count. Do not pad a JSONL corpus with fake entries.
- **Unexpected `allow_pickle` warning or security review failure** — keep the
  default `False`. Only use `True` for a trusted legacy NumPy object-array
  artifact whose provenance is known; never load an untrusted index with it.

## Large-index workflow failures

- **Memory remains high with `mmap=True`** — mapped pages are demand-loaded,
  query score accumulators and result arrays still use RAM, and BM25L/BM25+
  correction data is not mapped. Lower query batch size, omit the corpus when
  IDs suffice, or reload score arrays between batches.
- **Batch reload loses retrieval state** — `load_scores` refreshes only arrays.
  Keep the original loaded model, vocabulary, method, and `num_docs`; do not
  instantiate a default BM25 object and assume its parameters match.
- **Too many open files or locked temporary files** — close each
  `JsonlCorpus`, and call `load()` only after the previous mapping is closed if
  the platform requires it.
- **A routine check starts downloading NQ/BEIR** — stop it. The public large
  corpus examples are reference-only; persistence verification should use a
  tiny local fixture and no network.
