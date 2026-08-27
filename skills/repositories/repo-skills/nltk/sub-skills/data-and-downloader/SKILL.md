---
name: data-and-downloader
description: "Configure NLTK data search paths, download only needed NLTK data
  packages, locate/load resources with nltk.data, use corpus readers, and
  recover safely from missing, corrupt, stale, or unsafe data archives."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data And Downloader

Use this sub-skill when the task is about NLTK data packages rather than NLP algorithm usage: selecting targeted data downloads, setting `NLTK_DATA`/`nltk.data.path`, checking `nltk.data.find()` and `nltk.data.load()`, using `nltk.corpus` readers, diagnosing missing or corrupt resources, or recovering from downloader/path security failures.

Route away from this sub-skill when the task is mainly about:
- Tokenization, POS tagging, stemming, lemmatization, or VADER scoring after data is available: use `../tokenize-tag-stem/SKILL.md`.
- Grammars, parsers, trees, chunkers, semantics, or inference APIs: use `../grammar-parse-semantics/SKILL.md`.
- Classifiers, language models, metrics, probability distributions, or translation/alignment algorithms: use `../ml-metrics-and-translation/SKILL.md`.

## Fast Paths

- Install only the packages required by the failing API; do not recommend broad `all` unless the user explicitly wants the full collection. Common targeted packages: `punkt_tab`, `averaged_perceptron_tagger_eng`, `averaged_perceptron_tagger_rus`, `wordnet`, `omw-2.0`, `vader_lexicon`, `universal_tagset`, `brown`, `treebank`, `reuters`, and `comtrans`.
- Use `python -m nltk.downloader -d /path/to/nltk_data PKG...` or `import nltk; nltk.download("PKG", download_dir="/path/to/nltk_data")` for explicit downloads. Use `-q/--quiet`, `-f/--force`, `-e/--exit-on-error`, and `-u/--url` only when the task calls for them.
- For portable projects, set `NLTK_DATA=/path/to/nltk_data` before Python starts, or prepend the directory at runtime with `import nltk.data; nltk.data.path.insert(0, "/path/to/nltk_data")`.
- Probe resources before running an algorithm: `nltk.data.find("tokenizers/punkt_tab/english/")`, `nltk.data.find("taggers/averaged_perceptron_tagger_eng/")`, `nltk.data.find("corpora/wordnet/")`, or `nltk.data.find("sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt")`.
- Use corpus readers via `from nltk.corpus import brown, wordnet, reuters`; start with `fileids()`, `words()`, `sents()`, `tagged_words()`, `raw()`, `readme()`, and `categories()` where the reader supports them.
- Treat `LookupError` messages as package hints, but distinguish “package missing” from “package present but entry missing/corrupt”; stale/corrupt packages should be force-redownloaded into a controlled directory.
- For recovery from untrusted data inputs, reject traversal-like resource names, do not unzip arbitrary archives into `nltk_data`, and rely on the downloader’s validated extraction path instead of custom unsafe extraction.

## Reference Map

- Targeted package workflows, `NLTK_DATA` setup, downloader commands, corpus reader recipes, and safe recovery patterns: `references/data-workflows.md`.
- API signatures and resource/package map for `nltk.download`, `Downloader`, `nltk.data.find/load`, CLI flags, and common corpus reader methods: `references/api-reference.md`.
- LookupError diagnosis, read-only paths, proxy/network failures, stale/corrupt resources, package renames, and downloader/data security errors: `references/troubleshooting.md`.
- No-download checker for installed NLTK data paths and optional explicit download mode: `scripts/check_nltk_data.py`.

## Minimum Validation Pattern

1. Print `nltk.__version__`, Python version, `NLTK_DATA`, and the effective `nltk.data.path` before changing the environment.
2. Check exact resources with `nltk.data.find()` or the bundled no-download script; avoid importing a corpus reader as proof unless you also call a method such as `fileids()` or `words()[:5]`.
3. If a download is required, name explicit package IDs and use a controlled `download_dir`; re-run a no-download check afterward.
4. For corpus workflows, assert representative outputs and supported methods: e.g. `brown.fileids()`, `brown.words(fileids="ca01")`, `brown.tagged_words(tagset="universal")`, `wordnet.synsets("dog")`, `reuters.categories()`, or `comtrans.aligned_sents()[:1]` when the package is installed.
5. For security-sensitive recovery, ensure malformed resource strings fail closed (`ValueError`/`LookupError`) and archive extraction errors leave no partially trusted content to load.

Run the bundled checker from any current working directory after installing NLTK:

```bash
python /path/to/skills/disco/nltk/sub-skills/data-and-downloader/scripts/check_nltk_data.py --help
python /path/to/skills/disco/nltk/sub-skills/data-and-downloader/scripts/check_nltk_data.py --inspect
```
