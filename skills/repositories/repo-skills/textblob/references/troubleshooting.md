# TextBlob cross-cutting troubleshooting

Use this root guide for install/import/corpus/setup problems before routing to a
workflow-specific troubleshooting file.

## First response checklist

1. Confirm the target Python can import TextBlob:

   ```bash
   python - <<'PY'
   import textblob
   from importlib.metadata import version
   print(version("textblob"))
   print(textblob.__file__)
   PY
   ```

2. Run the bundled read-only setup check:

   ```bash
   python scripts/check_textblob_setup.py --json
   ```

3. If the task uses optional full-corpus features, also run:

   ```bash
   python scripts/check_textblob_setup.py --require-all-corpora --json
   ```

4. Route to the nearest sub-skill after setup is known:
   - Core TextBlob properties -> `sub-skills/core-nlp-workflows/references/troubleshooting.md`.
   - Word/WordNet/spelling/morphology -> `sub-skills/word-and-lexical-tools/references/troubleshooting.md`.
   - Classifiers and file formats -> `sub-skills/classifiers-and-data-formats/references/troubleshooting.md`.
   - Custom model/extension validation -> `sub-skills/custom-models-and-extensions/references/troubleshooting.md`.

## Import fails

### Symptom

`ModuleNotFoundError: No module named 'textblob'` or package metadata lookup
fails.

### Recovery

Install TextBlob in the exact environment running the task:

```bash
python -m pip install -U textblob
```

Then rerun the import check. Avoid mixing `pip` from one Python with `python`
from another; prefer `python -m pip`.

## `MissingCorpusError` after import succeeds

### Symptom

TextBlob imports, but `.words`, `.sentences`, `.tags`, `.noun_phrases`, WordNet,
`ConllExtractor`, or `NaiveBayesAnalyzer` fails with a missing corpus message.

### Recovery

Run corpus setup explicitly:

```bash
python -m textblob.download_corpora lite
```

For optional full-corpus workflows:

```bash
python -m textblob.download_corpora
```

Do not hide corpus downloads inside bundled smoke scripts or library code. They
are setup steps that may need network/cache access.

## Corpus command succeeds but Python still cannot find data

Possible causes:

- The download command ran in a different Python environment.
- `NLTK_DATA` points to a path unavailable to the runtime process.
- The process runs under a different user or container with a different NLTK
  data path.

Recovery:

```python
import nltk
print(nltk.data.path)
```

Run `python -m textblob.download_corpora` with the same `python` that runs the
workflow. If a custom `NLTK_DATA` directory is required, set it for both the
setup command and the runtime process.

## Optional numpy or MaxEnt issue

### Symptom

MaxEnt classifier training, NLTKTagger-related checks, or optional classifier
workflows fail with a numerical dependency/import error.

### Recovery

Install numpy in the target environment:

```bash
python -m pip install numpy
```

If the task does not require MaxEnt, route to `NaiveBayesClassifier` as the
bounded default classifier.

## Network-restricted setup

TextBlob's corpus downloader uses NLTK's downloader. In network-restricted
environments, download corpora in an approved environment/cache, configure
`NLTK_DATA`, and rerun the read-only setup check. Do not mark a corpus-backed
workflow verified until the exact runtime Python can find the required data.

## Version or API mismatch

This skill was built for TextBlob 0.20.1. If the target environment has a
significantly different TextBlob version, verify public signatures with:

```python
import inspect
from textblob import TextBlob, Word, Blobber
from textblob.classifiers import NaiveBayesClassifier
print(inspect.signature(TextBlob))
print(inspect.signature(Word))
print(inspect.signature(Blobber))
print(inspect.signature(NaiveBayesClassifier))
```

If constructors, default models, corpus names, or classifier behavior changed,
refresh this repo skill before relying on detailed guidance.

## Deprecated `clean_html`

`TextBlob(text, clean_html=True)` raises `NotImplementedError`. Strip HTML
before constructing a `TextBlob`, for example with an HTML parser such as
BeautifulSoup when that dependency is acceptable.

## No accelerator backend

TextBlob's selected public workflows are CPU/any-backend Python workflows. Do
not install CUDA, ROCm, MPS, or deep-learning stacks to use this skill unless a
separate downstream package requires them.
