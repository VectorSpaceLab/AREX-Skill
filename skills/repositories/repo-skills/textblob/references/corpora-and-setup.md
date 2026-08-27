# TextBlob corpora and setup

TextBlob's package import and its NLP behavior are separate readiness checks.
The package depends on NLTK, and several TextBlob properties need NLTK corpus or
model data at runtime.

## Install commands

For normal package use:

```bash
python -m pip install -U textblob
```

For source/development installs, install the package with the active Python's
package manager and then run the same corpus commands below. Do not rely on a
local repository checkout for normal TextBlob usage.

## Corpus commands

Default/basic workflows:

```bash
python -m textblob.download_corpora lite
```

Full TextBlob corpus set, including optional CoNLL and movie-review workflows:

```bash
python -m textblob.download_corpora
```

The package downloader covers these NLTK resource names:

| Corpus/model | Download mode | Needed by |
| --- | --- | --- |
| `brown` | lite and full | default `FastNPExtractor` noun phrases |
| `punkt_tab` | lite and full | default word/sentence tokenization |
| `wordnet` | lite and full | `Word.lemmatize`, `Word.synsets`, `Word.definitions`, direct WordNet APIs |
| `averaged_perceptron_tagger_eng` | lite and full | default `NLTKTagger` POS tags |
| `conll2000` | full only | `ConllExtractor` noun phrase extractor |
| `movie_reviews` | full only | `NaiveBayesAnalyzer` sentiment analyzer |

If a user needs only `TextBlob(...).sentiment` from the default
`PatternAnalyzer`, package import may be enough. If they need `.words`,
`.sentences`, `.tags`, `.noun_phrases`, WordNet, or corpus-trained optional
models, run corpus setup first.

## Optional dependencies

- `nltk>=3.9` is the package dependency.
- `numpy` is not needed for all TextBlob features, but TextBlob's public docs
  note that maximum entropy classifier workflows and NLTKTagger-related test
  coverage may require it. Install it when using `MaxEntClassifier` or when a
  target environment reports an NLTK/numpy import failure.
- TextBlob has no required CUDA, ROCm, MPS, TPU, or other accelerator backend.

## Read-only setup diagnostic

Run the bundled setup check from this skill directory or by absolute path:

```bash
python scripts/check_textblob_setup.py --json
python scripts/check_textblob_setup.py --require-all-corpora
```

The diagnostic imports TextBlob, checks expected NLTK resources, and runs tiny
TextBlob smokes. It never downloads corpora or mutates the environment.

Interpretation:

- Import failure: install TextBlob in the target Python environment.
- Missing lite corpus: run `python -m textblob.download_corpora lite`.
- Missing `conll2000` or `movie_reviews`: run `python -m textblob.download_corpora` when optional workflows require them.
- Smoke failure after corpora are present: route to the relevant sub-skill
  troubleshooting page because the issue is likely API use, custom model
  behavior, or data shape rather than setup.

## Environment hygiene for future agents

- Use `python -m pip` and `python -m textblob.download_corpora` with the exact
  Python environment that will run the workflow.
- Do not hide corpus downloads inside reusable scripts or library functions.
  They are network/cache-mutating setup steps and should be explicit.
- If `NLTK_DATA` is customized, ensure both the shell and Python process see it.
- When producing reproducible outputs, record whether corpus-backed features
  were used and which setup command was expected.
