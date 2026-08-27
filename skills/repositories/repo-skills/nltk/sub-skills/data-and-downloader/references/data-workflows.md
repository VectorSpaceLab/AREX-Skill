# NLTK Data Workflows

This reference covers operating workflows for NLTK 3.10.x data packages and corpus readers. It assumes the Python package `nltk` is already importable and does not require the original source checkout at runtime.

## Decide the smallest download set

Prefer targeted package IDs over `all`, `popular`, or `all-corpora` when a user reports a specific `LookupError`.

| User-facing need | Targeted package IDs | Probe before/after download | Notes |
| --- | --- | --- | --- |
| Sentence/word tokenizers that fail on Punkt data | `punkt_tab` | `tokenizers/punkt_tab/english/` | Current tokenizer resources use `punkt_tab`; older advice for `punkt` may not satisfy newer `word_tokenize`/`sent_tokenize` paths. |
| English POS tagging | `averaged_perceptron_tagger_eng` | `taggers/averaged_perceptron_tagger_eng/` | `pos_tag(..., lang="eng")` depends on the English perceptron tagger package. |
| Russian POS tagging | `averaged_perceptron_tagger_rus` | `taggers/averaged_perceptron_tagger_rus/` | Russian is selected with `lang="rus"` in tagger APIs; some compatibility loaders map older `ru` pickle requests to `rus`. |
| Universal POS tag mapping | `universal_tagset` | `taggers/universal_tagset/` or `taggers/universal_tagset.zip/universal_tagset/` | Needed when requesting `tagset="universal"` from taggers/corpora that support mapping. |
| WordNet synsets/lemmas | `wordnet` | `corpora/wordnet/` or `corpora/wordnet.zip/wordnet/` | Required for `nltk.corpus.wordnet` and `WordNetLemmatizer` behavior beyond simple fallback cases. |
| Multilingual WordNet names/lemmas | `omw-2.0` with `wordnet` | `corpora/omw-2.0/` or `corpora/omw-2.0.zip/omw-2.0/` | `nltk.corpus.wordnet` is constructed with an OMW lazy loader for multilingual data. |
| VADER sentiment lexicon | `vader_lexicon` | `sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt` | `SentimentIntensityAnalyzer` defaults to this zip-contained lexicon path. |
| Brown corpus examples | `brown` | `corpora/brown/` or `corpora/brown.zip/brown/` | Useful for tagged corpus examples and categories. |
| Penn Treebank sample | `treebank` | `corpora/treebank/combined/` or `corpora/treebank.zip/treebank/combined/` | Used by parse/tagged corpus examples. |
| Reuters categorized corpus | `reuters` | `corpora/reuters/` or `corpora/reuters.zip/reuters/` | Useful for categorized file/category workflows. |
| Translation aligned corpus | `comtrans` | `corpora/comtrans/` or `corpora/comtrans.zip/comtrans/` | Needed for corpus-backed translation/alignment examples; no-data algorithm examples route to `ml-metrics-and-translation`. |

## Download targeted packages

Python API:

```python
import nltk
nltk.download("punkt_tab", download_dir="/project/nltk_data", quiet=False)
nltk.download("averaged_perceptron_tagger_eng", download_dir="/project/nltk_data")
nltk.download("wordnet", download_dir="/project/nltk_data")
nltk.download("omw-2.0", download_dir="/project/nltk_data")
```

CLI equivalent:

```bash
python -m nltk.downloader -d /project/nltk_data punkt_tab averaged_perceptron_tagger_eng wordnet omw-2.0
```

Operational rules:

1. Use `-d/--dir` or `download_dir=` when the environment is read-only, containerized, shared, or needs reproducibility.
2. Use `-q/--quiet` for CI logs, `-f/--force` for stale/corrupt packages, `-e/--exit-on-error` when scripts should stop on the first failed package, and `-u/--url` or `NLTK_DOWNLOAD_URL` only for a trusted mirror/index.
3. Do not call `nltk.download()` with no argument in non-interactive automation; that opens an interactive GUI/shell if possible.
4. Do not download collections such as `all`, `all-corpora`, `popular`, or `book` unless the user accepts the size and broad surface area.
5. After any explicit download, run a no-download probe with `nltk.data.find()` or `scripts/check_nltk_data.py`.

## Configure search paths

NLTK builds `nltk.data.path` from `NLTK_DATA`, `~/nltk_data`, Python-prefix locations, and system locations such as `/usr/share/nltk_data` and `/usr/local/share/nltk_data` on Unix-like systems. It checks the list in order, so earlier directories can override later resources.

Set a project path before Python starts:

```bash
export NLTK_DATA=/project/nltk_data
python - <<'PY'
import nltk.data
print(nltk.data.path)
print(nltk.data.find("tokenizers/punkt_tab/english/"))
PY
```

Or prepend a path inside a process:

```python
import nltk.data
nltk.data.path.insert(0, "/project/nltk_data")
print(nltk.data.find("corpora/wordnet/"))
```

For multiple directories, join `NLTK_DATA` entries with the platform path separator (`:` on Unix/macOS, `;` on Windows). Keep `NLTK_DATA` pointed at the top-level `nltk_data` directory, not at `corpora/`, `tokenizers/`, or a package subdirectory.

## Find and load resources

Use `nltk.data.find(resource_name, paths=None)` to obtain a path pointer. Resource names are POSIX-style names such as `corpora/brown`, `tokenizers/punkt_tab/english/`, or explicit zip paths such as `sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt`.

```python
import nltk.data
ptr = nltk.data.find("corpora/brown/")
print(type(ptr).__name__, ptr)
```

Zip handling matters:

- If a resource name includes a `.zip` component, the remaining components are resolved inside that zip.
- If an element of `nltk.data.path` is itself a `.zip`, it is searched as a zip file.
- If a resource is not found unzipped, `find()` retries with `component.zip/component`, which lets `corpora/brown` resolve to `corpora/brown.zip/brown` when appropriate.
- When locating a directory inside a zip, include the trailing slash.

Use `nltk.data.load(resource_url, format="auto", cache=True, ...)` when you need parsed content instead of a pointer. The default `nltk:` protocol is used if no protocol is given. Supported formats include `pickle`, `json`, `yaml`, `cfg`, `pcfg`, `fcfg`, `fol`, `logic`, `val`, `raw`, and `text`; `auto` selects by extension. Use `format="raw"` for bytes and `format="text"` for decoded text.

```python
text = nltk.data.load("corpora/abc/rural.txt", format="text")
raw = nltk.data.load("corpora/abc/rural.txt", format="raw")
nltk.data.clear_cache()  # if checking a changed local file
```

Security notes for loading:

- Do not add spaces after `nltk:`; `nltk: tokenizers/...` is not the same resource URL.
- No-protocol absolute paths, drive-letter paths, backslash traversal, `..` traversal, and encoded traversal are rejected by current `nltk.data` checks.
- Since the 2024 pickle hardening, legacy unsafe pickle resources are replaced by pickle-free loader alternatives for Punkt, maxent chunker/treebank tagger, and averaged perceptron taggers where applicable; arbitrary pickle loading is restricted.

## Use corpus readers

Import corpus readers from `nltk.corpus`; most are `LazyCorpusLoader` proxies that load only when a method is first accessed.

```python
from nltk.corpus import brown, reuters, wordnet

print(brown.fileids()[:3])
print(brown.words("ca01")[:10])
print(brown.sents("ca01")[:1])
print(brown.tagged_words("ca01")[:5])
print(brown.tagged_words("ca01", tagset="universal")[:5])
print(brown.categories()[:5])

print(reuters.fileids("barley")[:3])
print(reuters.categories("training/9865"))
print(wordnet.synsets("dog")[:3])
```

Common reader methods and expected shapes:

- `fileids()` -> file identifier strings; often accepts a category or file-type filter.
- `abspath(fileid)` / `abspaths(fileids=None)` -> `PathPointer` objects for corpus files.
- `raw(fileids=None)` -> unprocessed text.
- `words(fileids=None)` -> flat token list/view.
- `sents(fileids=None)` -> list/view of tokenized sentences.
- `paras(fileids=None)` -> paragraphs, when the reader supports them.
- `tagged_words(...)`, `tagged_sents(...)`, `tagged_paras(...)` -> `(word, tag)` tuples for tagged corpora; optional `tagset="universal"` requires `universal_tagset`.
- `chunked_sents(...)` and `parsed_sents(...)` -> `Tree` objects for corpora that include chunks or parse trees.
- `readme()` -> README text where present.
- `categories()` / `fileids(categories=...)` -> categorized-corpus navigation where supported.

If a method is missing, the corpus reader type does not support that representation; route algorithm-level alternatives to the appropriate sub-skill instead of downloading more data blindly.

## Safe recovery checklist

1. Capture the exact exception and attempted resource path from the `LookupError`.
2. Print `NLTK_DATA` and `nltk.data.path`; verify the desired data directory is a top-level `nltk_data` directory and appears early enough in the path list.
3. Probe the exact package resource with `nltk.data.find()` or `check_nltk_data.py --inspect` without downloading.
4. If the package is absent, download exactly the named package into a controlled directory.
5. If the package appears installed but a sub-entry is missing, remove or force-redownload only that package; do not unzip a third-party archive by hand.
6. If the error mentions unsafe path, traversal, zip slip, symlink escape, null byte, cross-package overwrite, checksum/size mismatch, or sandbox/pathsec rejection, treat the resource or index as untrusted and stop until the data source is replaced with a trusted NLTK package or mirror.
