---
name: nltk
description: "Use NLTK for classical natural-language processing in Python:
  install the package and data, tokenize and tag text, stem or lemmatize, build
  grammars and parse trees, train classical models, score metrics, and work with
  translation alignments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# NLTK

Use this skill when a task names **NLTK** or asks for classical Python NLP workflows involving tokenization, corpora, POS tagging, stemming, parsing, grammar, text classification, sentiment, language models, translation metrics, or NLTK data packages.

NLTK 3.10.x is a broad toolkit rather than one end-to-end model. Start from the user's artifact and task: raw text, tokens, tagged sentences, a corpus/resource, a grammar, features, an aligned parallel corpus, or an evaluation score.

## Install and import check

NLTK supports Python 3.10 through 3.14. The base install provides `defusedxml`, `click`, `joblib`, `regex`, and `tqdm`.

```bash
python -m pip install nltk
python - <<'PY'
import nltk
print(nltk.__version__)
PY
```

Optional extras are deliberately separate: `machine_learning` (`numpy`, `python-crfsuite`, `scikit-learn`, `scipy`), `plot` (`matplotlib`), `tgrep` (`pyparsing`), `twitter` (`twython`), and `corenlp` (`requests`). Install only the extra or external tool the task requires.

NLTK code and NLTK data are separate. Do not treat `import nltk` as proof that `punkt_tab`, tagger models, corpora, WordNet, or VADER data are installed.

## Route by task

- **Install, locate, download, or repair corpora/models/data**: read [`sub-skills/data-and-downloader/SKILL.md`](sub-skills/data-and-downloader/SKILL.md). It covers `NLTK_DATA`, `nltk.data.path`, `nltk.data.find/load`, targeted downloader commands, corpus readers, and safe recovery.
- **Tokenize, detokenize, tag, stem, lemmatize, or run sentiment preprocessing**: read [`sub-skills/tokenize-tag-stem/SKILL.md`](sub-skills/tokenize-tag-stem/SKILL.md). It covers `word_tokenize`, `sent_tokenize`, the `nltk tokenize` CLI, `pos_tag`, tagger backoff, stemmers, WordNet lemmatization, and VADER.
- **Write grammars, chunk POS-tagged text, parse, manipulate trees, evaluate dependencies, or interpret logical semantics**: read [`sub-skills/grammar-parse-semantics/SKILL.md`](sub-skills/grammar-parse-semantics/SKILL.md).
- **Train classical classifiers, cluster vectors, fit n-gram language models, use probability distributions, score metrics, or build translation alignments**: read [`sub-skills/ml-metrics-and-translation/SKILL.md`](sub-skills/ml-metrics-and-translation/SKILL.md).

For a pipeline that spans routes, use them in order: data/resource checks → tokenization/tagging → grammar or feature construction → model/metric evaluation. Keep each stage's input shape explicit.

## Shared operating rules

1. Prefer small, deterministic, no-download checks before downloading data or installing optional dependencies.
2. When a `LookupError` names an attempted resource, use that exact path to choose the smallest package; do not default to `all` or `popular`.
3. Preserve tokenization and tagset choices in outputs. A parser, classifier, or metric is not comparable if preprocessing changes silently.
4. Treat third-party Java/binary wrappers, GUI apps, network downloads, credentials, and large corpora as explicit optional prerequisites.
5. Never manually unzip untrusted NLTK packages or bypass `nltk.data` path-security checks.

## Shared references and diagnostics

- Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting installation, data, optional-dependency, API-shape, CLI, and security failures.
- Read [`references/native-verification.md`](references/native-verification.md) when selecting a safe smoke or native test; it records what was verified and what remains data- or tool-dependent.
- Run [`scripts/nltk_doctor.py`](scripts/nltk_doctor.py) with `--help` first, then `--json` for a read-only import/CLI/resource diagnostic. It never downloads data unless `--download` is explicitly supplied.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill matches a changed NLTK checkout or should be refreshed.

## Boundaries

This is a runtime package skill, not a release or contributor manual. It does not bundle NLTK corpora, Java tools, Stanford/CoreNLP/Senna/Malt/MEGAM/TADM binaries, GUI assets, credentials, or the original repository's tests/docs. Those artifacts informed the routes and verification plan; runtime helpers and distilled references live inside this skill tree.
