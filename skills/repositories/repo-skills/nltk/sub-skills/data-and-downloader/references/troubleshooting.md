# Data And Downloader Troubleshooting

Use this guide to recover NLTK data problems without reopening the source repository and without broad or unsafe downloads.

## `LookupError: Resource ... not found`

1. Copy the attempted resource path from the error, not just the package hint.
2. Print the effective path list:

   ```python
   import os, nltk.data
   print("NLTK_DATA=", os.environ.get("NLTK_DATA"))
   print("nltk.data.path=", nltk.data.path)
   ```

3. Probe the exact resource with `nltk.data.find(...)` or:

   ```bash
   python scripts/check_nltk_data.py --inspect --package punkt_tab --package wordnet
   ```

4. Download the smallest package ID into a controlled top-level `nltk_data` directory:

   ```bash
   python -m nltk.downloader -d /project/nltk_data punkt_tab
   export NLTK_DATA=/project/nltk_data
   ```

5. Re-run the no-download probe before re-running the NLP task.

Common fixes:

| Symptom | Targeted fix |
| --- | --- |
| `word_tokenize` / `sent_tokenize` asks for Punkt tables | `nltk.download("punkt_tab", download_dir=...)` |
| `pos_tag` English tagger missing | `nltk.download("averaged_perceptron_tagger_eng", download_dir=...)` |
| `pos_tag(..., lang="rus")` missing | `nltk.download("averaged_perceptron_tagger_rus", download_dir=...)` |
| `tagset="universal"` mapping missing | `nltk.download("universal_tagset", download_dir=...)` |
| `WordNetLemmatizer` or `nltk.corpus.wordnet` missing | `nltk.download("wordnet", download_dir=...)` |
| WordNet multilingual lemmas/names missing | `nltk.download("omw-2.0", download_dir=...)` in addition to `wordnet` |
| `SentimentIntensityAnalyzer` missing lexicon | `nltk.download("vader_lexicon", download_dir=...)` |
| Brown/Treebank/Reuters/Comtrans corpus examples fail | Download the corresponding package ID only. |

## Wrong `NLTK_DATA` or data path order

Problems:

- `NLTK_DATA` points to `.../nltk_data/corpora` instead of top-level `.../nltk_data`.
- A stale user directory appears before a fresh project directory in `nltk.data.path`.
- `NLTK_DATA` was set after `nltk.data` was imported, so the current process did not pick it up.
- A container or CI job downloads to one directory but runs tests with a different environment.

Recovery:

```python
import nltk.data
nltk.data.path[:] = ["/project/nltk_data", *[p for p in nltk.data.path if p != "/project/nltk_data"]]
print(nltk.data.find("corpora/wordnet/"))
```

For shell workflows:

```bash
export NLTK_DATA=/project/nltk_data
python -m nltk.downloader -d "$NLTK_DATA" wordnet omw-2.0
python /absolute/path/to/check_nltk_data.py --data-dir "$NLTK_DATA" --inspect --package wordnet --package omw-2.0
```

## Read-only or shared installation directories

`Downloader.default_download_dir()` prefers existing writable locations from `nltk.data.path`, then a user home directory. On managed machines this can choose a read-only or shared path unexpectedly.

Use a controlled project/user directory:

```bash
mkdir -p "$PWD/.nltk_data"
python -m nltk.downloader -d "$PWD/.nltk_data" punkt_tab averaged_perceptron_tagger_eng
export NLTK_DATA="$PWD/.nltk_data"
```

In Python:

```python
import nltk
nltk.download("punkt_tab", download_dir="/project/.nltk_data", quiet=True)
```

Avoid `sudo` unless central installation is intentional and the same path is readable by all runtime users.

## Proxy, mirror, and network failures

For authenticated or corporate proxies, configure NLTK before downloading:

```python
import nltk
nltk.set_proxy("http://proxy.example.com:3128", ("USERNAME", "PASSWORD"))
nltk.download("wordnet", download_dir="/project/nltk_data")
```

For a trusted internal mirror/index:

```bash
export NLTK_DOWNLOAD_URL=https://mirror.example.org/nltk_data/index.xml
python -m nltk.downloader -d /project/nltk_data -u "$NLTK_DOWNLOAD_URL" wordnet
```

If a downloader test or fixture uses a `file://` URL and `pathsec.urlopen` refuses a proxied fetch, the active proxy is blocking SSRF-sensitive egress validation. Keep the check offline or, only when the proxy is trusted and the task explicitly requires it, opt in with `NLTK_ALLOW_PROXIED_URLOPEN=1` or `nltk.pathsec.ALLOW_PROXIED_FETCH=True`.

Do not use an untrusted index or package mirror. Current downloader code performs size/checksum validation and safer extraction, but the package source still defines what data will be trusted by downstream workflows.

## Stale, corrupt, or partially installed packages

Signals:

- Downloader status says `out of date`, `partial`, or package did not reach installed state.
- `find()` reports the package appears installed but a requested entry is missing.
- A zip exists but the unzipped directory size/checksum does not match metadata.
- A prior process was interrupted while downloading or unzipping.

Recovery:

```bash
python -m nltk.downloader --force -d /project/nltk_data wordnet
python /absolute/path/to/check_nltk_data.py --data-dir /project/nltk_data --require --package wordnet
```

If force-redownload fails with the same corruption, delete only the affected package zip/directory under the appropriate subdir (`corpora/wordnet.zip`, `corpora/wordnet/`, etc.) and retry from a trusted index. Do not delete unrelated packages or global data roots.

## Zip extraction and path security errors

Current downloader/data behavior is intentionally fail-closed for unsafe paths. Treat these errors as security signals, not ordinary missing data:

- `Path traversal blocked`
- `Zip Slip blocked`
- `Symlink escape blocked`
- `Null byte in entry name blocked`
- `Cross-package overwrite blocked`
- checksum or size mismatch
- `Unsafe resource path`
- pathsec `PermissionError`/security violation

Recovery policy:

1. Stop using the suspect archive, data directory, or index URL.
2. Remove any partial target for that single package from the controlled `download_dir`.
3. Retry from the default NLTK index or another trusted mirror.
4. Keep `NLTK_DATA` pointed at directories you control; do not include world-writable or user-supplied paths ahead of trusted data.
5. Never manually unzip a package into `nltk_data` to bypass downloader validation.

## Unsafe resource URL patterns

`nltk.data.normalize_resource_url`, `find`, and `load` reject traversal and absolute local paths in no-protocol or `nltk:` resource strings. Examples that should fail include:

- `../../etc/passwd`
- `../relative/../etc/passwd`
- `C:/etc/passwd` or `C:\\etc\\passwd` without explicit safe intent
- `nltk:%2fetc%2fpasswd`
- `nltk:corpora/%2e%2e/%2e%2e/etc/passwd`

Safe encoded names such as spaces or non-ASCII package components may still normalize as NLTK resources. If a user truly needs to read a local file, use an explicit `file:` URL or normal Python file I/O under the runtime's sandbox policy, not an `nltk:` resource path.

## Corpus reader method errors

`AttributeError` on a corpus method usually means the reader type does not expose that representation. Examples:

- Plaintext readers commonly have `words()`, `sents()`, `paras()`, and `raw()`, but not `tagged_words()`.
- Tagged readers expose `tagged_words()`/`tagged_sents()`; universal tag conversion additionally needs `universal_tagset`.
- Chunked or parsed methods are limited to chunk/treebank-style readers.
- Categorized readers expose `categories()` and category-filtered `fileids()`.

Do not download extra packages until the reader type and requested method are compatible. Use `fileids()`, `readme()`, and a small method call as the first diagnostic.

## Lazy corpus loader surprises

NLTK corpus module attributes often start as `LazyCorpusLoader` objects. Loading occurs when a non-dunder method is accessed, and `_unload()` can restore a lazy proxy. Tests verify that dunder introspection such as `__wrapped__` should not trigger loading. If debugging a lazy loader:

```python
from nltk.corpus import brown
print(repr(brown))       # may say not loaded yet
print(brown.fileids()[:1])
print(repr(brown))       # now a concrete reader
brown._unload()          # diagnostic only; not typical user code
```

If loading fails, return to exact `LookupError` package/resource diagnosis rather than assuming the lazy loader is broken.

## `nltk.data.load` format errors

- `ValueError: Unknown format type` means the explicit format is not one of `pickle`, `json`, `yaml`, `cfg`, `pcfg`, `fcfg`, `fol`, `logic`, `val`, `raw`, or `text`.
- `Could not determine format ... based on its file extension` means `format="auto"` cannot infer the type; pass `format="raw"`, `format="text"`, or another explicit format.
- Cache confusion after editing a local resource can be fixed with `cache=False` for that load or `nltk.data.clear_cache()`.

## Pickle-related failures

Current NLTK restricts unpickling and routes several legacy pickle resource paths to pickle-free alternatives. If old code tries to load a model pickle directly:

1. Prefer the public high-level API (`PunktTokenizer`, `pos_tag`, named entity chunker, etc.).
2. Install the current non-pickle data package (`punkt_tab`, language-specific perceptron tagger packages) instead of resurrecting old pickle files.
3. Do not disable pickle restrictions to load untrusted data.
