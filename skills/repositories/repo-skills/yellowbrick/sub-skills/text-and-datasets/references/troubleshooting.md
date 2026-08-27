# Yellowbrick text and dataset troubleshooting

Use this page after a Yellowbrick dataset loader, dataset cache operation, or
text visualizer fails. For package-wide import, scikit-learn compatibility,
Matplotlib backend, style, and display failures, also read the root
[troubleshooting reference](../../../references/troubleshooting.md).

## Dataset cache, download, and offline failures

| Symptom | Likely cause | Concrete fix |
|---|---|---|
| `DatasetsError: could not find dataset at ... does it need to be downloaded?` | The selected cache directory exists, but the requested dataset file such as `.csv.gz`, `.npz`, `README.md`, or `meta.json` is missing. | Inspect the cache with `scripts/check_dataset_cache.py`; point `data_home`/`YELLOWBRICK_DATA` at a complete cache or run the downloader only if the user approves network access. |
| Loader tries to access the network in an offline task | The dataset directory is absent; loader construction triggers Yellowbrick's downloader. | Do not call the loader until the cache inspector shows the dataset directory is present. Use `data_home=` or `YELLOWBRICK_DATA` to select a pre-populated cache. |
| Cache root is not where the user expected | An explicit `data_home` argument or `YELLOWBRICK_DATA` overrides the default package fixture directory. | Explain resolution order: `data_home`, then `YELLOWBRICK_DATA`, then package default. Print or inspect the selected cache before loading. |
| `Download signature does not match hardcoded signature!` | A downloaded archive is corrupt, incomplete, stale, or not the expected Yellowbrick archive. | Treat as a cache-integrity issue. Inspect the archive signature, remove/replace the bad archive only with user approval, then rerun a real download in a network-enabled environment if desired. |
| Cache inspector reports `signature-mismatch` | Local `<dataset>.zip` hash differs from the manifest signature. | Do not use the archive as trusted evidence. Choose a different cache or ask the user whether to delete/re-download outside the read-only inspector. |
| `dataset already exists ...` during download | The archive already exists and the downloader was called without replacement enabled. | Use `python -m yellowbrick.download --overwrite` only when the user intentionally wants to replace existing cached material. Do not use overwrite in a smoke check. |
| User wants to clear old cache data | Cleanup is a destructive downloader operation, not a loader setting. | If the user explicitly approves cleanup, use `python -m yellowbrick.download --cleanup --no-download [data_home]`; otherwise stay read-only and inspect. |
| `load_hobbies()` does not unpack into `X, y` | `load_hobbies()` returns a `Corpus` object by design. | Use `corpus.data`, `corpus.target`, `corpus.labels`, and `corpus.files`; vectorize `corpus.data` before FreqDist/TSNE/UMAP. |
| Loader returns numpy arrays instead of pandas objects | `pandas` is not installed. | This is expected fallback behavior. Install `pandas` if DataFrames are required, or use the numpy arrays / `Dataset.to_numpy()`. |
| `to_dataframe()` or `to_pandas()` fails because pandas is required | The minimum environment does not include `pandas`. | Use default `X, y` or `to_numpy()`; only promise DataFrame/Series output after confirming `pandas` is importable. |

## Dataset-specific modeling traps

- `load_game()` and `load_mushroom()` contain categorical features; add encoding
  before most scikit-learn estimators.
- `load_credit()` and `load_walking()` are large enough that expensive CV,
  TSNE, or manifold visualizers should sample or use bounded parameters.
- `load_energy()` source material includes multiple targets; the default loader
  returns the documented primary target.
- `load_hobbies()` is text data; vectorize or tokenize before text visualizers.
- Missing cache files are not fixed by changing model parameters. Fix the cache
  or choose a loader whose cache is complete.

## Text visualizer name and input errors

| Symptom | Likely cause | Concrete fix |
|---|---|---|
| `ImportError` or `AttributeError` for `FrequencyVisualizer` | The public top-level name is `FreqDistVisualizer`, not `FrequencyVisualizer`. | Use `from yellowbrick.text import FreqDistVisualizer`. Mention the old implementation alias only as legacy context. |
| `FreqDistVisualizer` shows no expected words | Vectorizer preprocessing removed the terms, or feature names do not match matrix columns. | Inspect `vectorizer.get_feature_names_out()`, adjust `stop_words`, `token_pattern`, `min_df`, or preprocessing, and pass the matching feature list. |
| Old examples/tests fail with `CountVectorizer` missing `get_feature_names` | scikit-learn removed `get_feature_names()` in favor of `get_feature_names_out()`. | Update the snippet to `vectorizer.get_feature_names_out()` or use a small compatibility helper that falls back only when the new method is absent. |
| Conditional frequency plot fails or ignores labels | `y` is a plain list or has shape/indexing that does not mask the sparse matrix correctly. | Convert labels to a numpy array or pandas Series aligned with rows of `X`. |
| `TSNEVisualizer` is slow, unstable, or errors on tiny data | t-SNE is expensive and `perplexity` must be smaller than the sample count; decomposition size may be too large. | Vectorize first, sample rows, set a small `perplexity` for small corpora, and reduce `decompose_by` or use `decompose=None` when appropriate. |
| `UMAPVisualizer` raises that UMAP is not installed | Optional `umap-learn` dependency is missing. | Install `umap-learn` only in a user-approved environment, or fall back to `TSNEVisualizer`. |
| `DispersionPlot` says a search term is not found | Search terms did not survive tokenization or casing, or input was raw strings instead of token lists. | Pass tokenized documents (`list[list[str]]` or generator of token lists), use `ignore_case=True`, and choose terms known to appear. |
| `DispersionPlot` raises `TypeError: arrays to stack must be passed as a sequence` | Yellowbrick 1.5's internal generator stack path is incompatible with some newer NumPy versions. | Use `WordCorrelationPlot` for the no-optional smoke requirement, or run DispersionPlot in a compatibility-pinned environment / patched Yellowbrick build. |
| `WordCorrelationPlot` raises `Word '<term>' does not exist in the corpus.` | One or more requested words/phrases is absent after vectorization. | Confirm terms appear in raw documents, align casing with `ignore_case`, and reduce the term list. |
| `WordCorrelationPlot([])` or blank words raises an error | The visualizer requires at least one non-empty term. | Provide a non-empty list of words or phrases. |
| Multi-word phrase correlations fail unexpectedly | N-gram range is inferred from requested terms, but the phrase does not occur in the corpus. | Check the exact phrase, punctuation, and casing in raw strings; simplify to single words if needed. |

## POS tagging parser and tagset errors

| Symptom | Likely cause | Concrete fix |
|---|---|---|
| `YellowbrickValueError` for unknown tagset such as `brill` | `PosTagVisualizer` only accepts `penn_treebank` and `universal`. | Use `tagset="penn_treebank"` for Penn/NTLK-style tags or `tagset="universal"` for Universal Dependencies tags. |
| `ModuleNotFoundError` for `nltk` or `spacy` parser mode | The optional parser library is not installed. | Use parser-free pre-tagged nested tuples, or install the parser package in a user-approved environment. |
| NLTK parser mode raises a Treebank/tokenizer lookup error | The Python package exists but required NLTK data is not installed. | Avoid downloads in a smoke check; use pre-tagged tuples. If the user wants raw parsing, install/download NLTK data explicitly outside read-only validation. |
| SpaCy parser mode raises that a model has not been downloaded | The named SpaCy model, often `en_core_web_sm`, is missing. | Use pre-tagged tuples or install the model in an approved environment. |
| `ValueError` for NLTK tagger name | The parser string after `nltk_` is not `word` or `wordpunct`. | Use `parser="nltk"`, `parser="nltk_word"`, or `parser="nltk_wordpunct"`. |
| `ValueError` for invalid parser | Parser must start with `nltk` or `spacy`. | Use supported parser strings or feed pre-tagged data with `parser=None`. |
| `Specify y for stack=True` | Stacked POS bar mode needs labels for each document. | Pass `y` with one label per document or set `stack=False`. |
| Counts look wrong with parser-free input | Tuple order or nesting is wrong. | Use `list[document][sentence][(token, tag)]`; each tag should match the selected tagset. |

## Matplotlib display, backend, and font symptoms

| Symptom | Likely cause | Concrete fix |
|---|---|---|
| `cannot connect to display`, blank windows, or hangs in CI | Interactive Matplotlib backend was selected in a headless environment. | Set `matplotlib.use("Agg")` before importing `matplotlib.pyplot` or Yellowbrick visualizers, then save with `show(outpath=...)`. |
| PNG file is missing after a quick method | Quick methods call `show()` by default and are less predictable for report output. | Prefer class API, or call quick method with `show=False` and then `viz.show(outpath=..., clear_figure=True)`. |
| Font warnings such as missing generic `sans-serif` | The environment lacks Matplotlib's preferred fonts. | Usually not fatal if the PNG is written. Use root troubleshooting for font installation or style changes when visual quality matters. |
| Overlapping figures or memory growth in a loop | Figures are not cleared/closed after saving. | Call `show(outpath=..., clear_figure=True)` and close figures in scripts that create many plots. |
| Non-ASCII labels render poorly | Font coverage is incomplete. | Choose a font with the needed glyphs or treat warnings as cosmetic if output is otherwise valid. |

## Safe helper scripts

- `scripts/check_dataset_cache.py` is a no-download, no-delete JSON cache
  inspector. It supports `--data-home` and repeated `--dataset` flags. Exit code
  `0` means inspection completed for valid names; `1` means Yellowbrick metadata
  could not be imported or an unexpected inspection error occurred; `2` means an
  unknown dataset name was requested.
- `scripts/text_smoke.py` uses Matplotlib `Agg` and inline synthetic documents to
  render `FreqDistVisualizer`, `TSNEVisualizer`, `DispersionPlot`,
  `WordCorrelationPlot`, and a parser-free `PosTagVisualizer`. It skips
  `UMAPVisualizer` when `umap-learn` is absent and does not load Yellowbrick
  datasets, run the downloader, or fetch parser data.

## Font warnings

Some headless inspection environments print `findfont` or generic sans-serif
warnings even when the PNG files are written correctly. Treat those messages as
non-fatal unless the file is missing, empty, or the plot looks wrong. If the
warning is accompanied by a missing image or a real render failure, escalate to
the root troubleshooting reference.

## Escalation checklist

Escalate to root troubleshooting when:

- `import yellowbrick` fails;
- Matplotlib cannot import or save any plot;
- scikit-learn/numpy compatibility breaks unrelated Yellowbrick visualizers;
- the failure is a general display/font/backend problem rather than a text or
  dataset API problem.
