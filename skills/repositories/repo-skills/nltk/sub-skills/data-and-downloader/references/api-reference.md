# Data And Downloader API Reference

Version evidence from the prepared inspection environment: NLTK `3.10.2` on Python `3.13.14`. The workflows below use public package APIs and do not require the original checkout at runtime.

## Downloader API

Top-level import:

```python
import nltk
nltk.download(info_or_id=None, download_dir=None, quiet=False, force=False,
              prefix="[nltk_data] ", halt_on_error=True,
              raise_on_error=False, print_error_to=sys.stderr, hf=False)
```

Behavior:

- `info_or_id=None` opens the interactive downloader GUI/shell; avoid this in automation.
- `info_or_id` can be a package ID such as `punkt_tab` or a collection ID such as `popular`.
- `download_dir` overrides the default installation directory for this call.
- `quiet=True` suppresses normal progress output.
- `force=True` redownloads even if the package appears installed.
- `halt_on_error=True` returns `False` on the first error; `raise_on_error=True` raises `ValueError` instead.
- `hf=True` delegates package retrieval to the NLTK Hugging Face dataset bridge for supported resources.

Object API:

```python
from nltk.downloader import Downloader

d = Downloader(server_index_url=None, download_dir=None)
d.list(skip_installed=True)
d.packages(); d.collections(); d.corpora(); d.models()
d.info("wordnet")
d.status("wordnet")       # "installed", "not installed", "out of date", or "partial"
d.is_installed("wordnet")
d.update(quiet=True)       # redownloads packages whose status is stale
```

Status checks may need the downloader index. For purely local, no-network checks, prefer `nltk.data.find()` probes.

## Downloader CLI

Canonical command:

```bash
python -m nltk.downloader [OPTIONS] PACKAGE_IDS...
```

Supported flags from the repository parser:

| Flag | Meaning |
| --- | --- |
| `-d DIR`, `--dir DIR` | Download packages to directory `DIR`. |
| `-q`, `--quiet` | Work quietly. |
| `-f`, `--force` | Download even if already installed. |
| `-e`, `--exit-on-error` | Exit if an error occurs. |
| `-u URL`, `--url URL` | Use an alternate downloader index URL; default can also come from `NLTK_DOWNLOAD_URL`. |

Examples:

```bash
python -m nltk.downloader -d /project/nltk_data punkt_tab averaged_perceptron_tagger_eng
python -m nltk.downloader --quiet --exit-on-error -d /project/nltk_data wordnet omw-2.0
python -m nltk.downloader --force -d /project/nltk_data vader_lexicon
```

## Data search path API

`nltk.data.path` is a mutable list of search directories. It is initialized from:

1. `NLTK_DATA` entries split by the platform path separator.
2. `~/nltk_data` when a home directory is available.
3. Windows prefix/appdata/common drive locations, or Unix/macOS Python-prefix and system locations such as `/usr/share/nltk_data` and `/usr/local/share/nltk_data`.

Use:

```python
import os
import nltk.data

print(os.environ.get("NLTK_DATA"))
print(nltk.data.path)
nltk.data.path.insert(0, "/project/nltk_data")
```

If the environment variable is set after `nltk.data` has already been imported, update `nltk.data.path` explicitly in that process.

## `nltk.data.find`

Signature from installed facts:

```python
nltk.data.find(resource_name, paths=None)
```

Key behavior:

- Accepts POSIX-style resource names such as `corpora/brown`, `tokenizers/punkt_tab/english/`, or `taggers/averaged_perceptron_tagger_eng/`.
- Returns a path pointer such as `FileSystemPathPointer`, `GzipFileSystemPathPointer`, or `ZipFilePathPointer`.
- Searches each entry in `paths` or `nltk.data.path`.
- Handles zip files explicitly (`corpora/brown.zip/brown/...`) and by fallback (`corpora/brown/...` can map to `corpora/brown.zip/brown/...`).
- Directory resources inside zip files require a trailing slash.
- Raises `LookupError` with a downloader hint when missing.
- Raises `ValueError` for unsafe absolute/traversal/no-protocol/encoded traversal names.

Common probes:

```python
nltk.data.find("tokenizers/punkt_tab/english/")
nltk.data.find("taggers/averaged_perceptron_tagger_eng/")
nltk.data.find("taggers/averaged_perceptron_tagger_rus/")
nltk.data.find("taggers/universal_tagset/")
nltk.data.find("corpora/wordnet/")
nltk.data.find("corpora/omw-2.0/")
nltk.data.find("sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt")
```

## `nltk.data.load`

Signature from installed facts:

```python
nltk.data.load(resource_url, format="auto", cache=True, verbose=False,
               logic_parser=None, fstruct_reader=None, encoding=None)
```

Supported formats from `nltk.data.FORMATS`:

- `pickle`, `json`, `yaml`
- `cfg`, `pcfg`, `fcfg`
- `fol`, `logic`, `val`
- `raw`, `text`

Auto-extension mapping includes `.pickle`, `.json`, `.yaml`, `.cfg`, `.pcfg`, `.fcfg`, `.fol`, `.logic`, `.val`, `.txt`, and `.text`.

Examples:

```python
import nltk.data

cfg = nltk.data.load("grammars/sample_grammars/toy.cfg")
text = nltk.data.load("corpora/abc/rural.txt", format="text")
raw = nltk.data.load("corpora/abc/rural.txt", format="raw")
nltk.data.clear_cache()
```

Security and compatibility:

- A resource URL without protocol defaults to `nltk:`.
- `file:` URLs can load local files, subject to the runtime path security policy.
- Current code rejects traversal-like resource strings and URL-encoded traversal attempts.
- `pickle` loading is restricted; known old pickle resource URLs for Punkt, named entity chunker, treebank POS tagger, and averaged perceptron taggers are switched to pickle-free alternatives where possible.

## Corpus reader API patterns

Corpus objects in `nltk.corpus` are usually lazy loaders. Accessing non-dunder attributes or methods loads the underlying reader; tests verify that representation and dunder introspection should not trigger loading, and `_unload()` can restore the lazy proxy.

Common methods and contracts:

| Method | Typical result | Notes |
| --- | --- | --- |
| `fileids(...)` | list of file IDs | May accept category or extension filters depending on reader. |
| `abspath(fileid)` / `abspaths(fileids=None)` | path pointer(s) | Useful for debug and custom readers. |
| `raw(fileids=None)` | raw text string | Plain text and many categorized corpora. |
| `words(fileids=None)` | flat words/tokens | Often lazy corpus views, not necessarily materialized lists. |
| `sents(fileids=None)` | list/view of token lists | Sentence-tokenized corpora. |
| `paras(fileids=None)` | nested paragraph/sentence/token structure | Only some readers. |
| `tagged_words(..., tagset=None)` | `(word, tag)` tuples | `tagset="universal"` needs `universal_tagset` when supported. |
| `tagged_sents(..., tagset=None)` | sentence lists of tagged tuples | For tagged corpora. |
| `chunked_sents(...)` | `Tree` objects | Chunked corpora only. |
| `parsed_sents(...)` | parse `Tree` objects | Treebank-style corpora only. |
| `readme()` | README text | Only if the corpus package has a README. |
| `categories(...)` | category labels | Categorized readers such as Brown/Reuters/Movie Reviews. |

Selected corpus loader IDs from `nltk/corpus/__init__.py`:

- `brown` -> package root `corpora/brown`, categorized tagged reader, Brown tagset by default.
- `comtrans` -> package root `corpora/comtrans`, aligned corpus reader.
- `reuters` -> package root `corpora/reuters`, categorized plaintext reader.
- `treebank` -> package root `corpora/treebank/combined`, bracket parse corpus reader.
- `wordnet` -> package root `corpora/wordnet`, WordNet reader with a lazy `omw-2.0` reader for multilingual data.

## Package and resource map

| Package ID | Primary subdir | Useful resource paths |
| --- | --- | --- |
| `punkt_tab` | `tokenizers` | `tokenizers/punkt_tab/english/` |
| `averaged_perceptron_tagger_eng` | `taggers` | `taggers/averaged_perceptron_tagger_eng/` |
| `averaged_perceptron_tagger_rus` | `taggers` | `taggers/averaged_perceptron_tagger_rus/` |
| `universal_tagset` | `taggers` | `taggers/universal_tagset/`, `taggers/universal_tagset.zip/universal_tagset/` |
| `wordnet` | `corpora` | `corpora/wordnet/`, `corpora/wordnet.zip/wordnet/` |
| `omw-2.0` | `corpora` | `corpora/omw-2.0/`, `corpora/omw-2.0.zip/omw-2.0/` |
| `vader_lexicon` | `sentiment` | `sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt`, `sentiment/vader_lexicon/vader_lexicon.txt` |
| `brown` | `corpora` | `corpora/brown/`, `corpora/brown.zip/brown/` |
| `treebank` | `corpora` | `corpora/treebank/combined/`, `corpora/treebank.zip/treebank/combined/` |
| `reuters` | `corpora` | `corpora/reuters/`, `corpora/reuters.zip/reuters/` |
| `comtrans` | `corpora` | `corpora/comtrans/`, `corpora/comtrans.zip/comtrans/` |

When a probe fails, use the package ID in `nltk.download("...")`; when a corpus method fails, map the corpus reader back to its package root before downloading.
