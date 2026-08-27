# NLTK Verification Baseline

This reference records the safe behavior checks used while creating this skill. It is not a replacement for a full NLTK test suite and does not require the original checkout at runtime.

## Prepared environment facts

- Distribution: `nltk 3.10.2`.
- Python compatibility: repository metadata supports Python 3.10–3.14; the inspection runtime was Python 3.13.
- Base dependencies imported successfully: `defusedxml`, `click`, `joblib`, `regex`, `tqdm`.
- Required backend: CPU/ordinary Python only. NLTK core workflows do not require CUDA, ROCm, MPS, or another accelerator.
- Optional capabilities not in the minimum environment: NumPy/scikit-learn/SciPy/CRFSuite, plotting/Tkinter, Twitter, Java/Stanford/CoreNLP/Senna/Malt/BLLIP/Prover9/Mace4/Weka/MEGAM/TADM wrappers, and NLTK data downloads.

## Safe checks passed

- `import nltk`, `nltk.tokenize`, `nltk.data`, `nltk.downloader`, and `nltk.corpus`.
- `nltk --help`, `nltk tokenize --help`, and `python -m nltk.downloader --help`.
- No-download tokenizer/stemmer/tagger-backoff checks.
- `nltk tokenize` stdin/output check with `--preserve-line` and a custom delimiter.
- In-memory CFG/chart/recursive-descent/shift-reduce/PCFG/feature-grammar, chunk, tree, dependency, logic, and DRT checks.
- In-memory Naive Bayes, frequency/probability, smoothed language-model, metric, BLEU, alignment, AER, and IBM Model 1 checks.
- Data/security evidence for exact resource lookup, traversal rejection, safe archive extraction, symlink containment, and XML entity-expansion rejection was inspected from the repository tests; network downloads were not required for skill drafting.

## Data-dependent checks

These are valid routes but require the named data packages before execution:

| Workflow | Resource(s) |
| --- | --- |
| Sentence splitting/default word tokenization | `punkt_tab` |
| English/Russian pretrained POS tagging | `averaged_perceptron_tagger_eng`, `averaged_perceptron_tagger_rus` |
| Universal tag conversion | `universal_tagset` |
| WordNet/lemmatization | `wordnet`, optionally `omw-2.0` |
| VADER | `vader_lexicon` |
| Corpus examples | `brown`, `treebank`, `reuters`, `comtrans`, or the corpus named by the task |

Use the no-download checker in `sub-skills/data-and-downloader/scripts/check_nltk_data.py` before an operation. A missing resource is an explicit data prerequisite, not a failure of the Python package itself.

## Native ground-truth verification

The production verification selected focused CLI/unit candidates from the NLTK repository after whole-skill integration. The safe selected checks passed for: root and tokenizer CLI help, downloader CLI help, the bundled root/data/tokenize/grammar/ML smoke scripts, short CLI tokenizer regressions, tweet tokenizer behavior, German Snowball stemming, `nltk.data` lookup and path-security behavior, downloader unzip/symlink/XXE/atomic safety fixtures, lazy corpus utility behavior, and regexp chunking.

Optional MEGAM/TADM classifier tests were not selected as required evidence because they need external binaries and the generated minimum ML route uses pure-Python classifiers plus the bundled no-download ML smoke. Broad corpus-backed doctests, GUI apps, Java/service wrappers, and broad data downloads remain data/tool-dependent long-tail items.

## Interpretation

- A passing no-download smoke proves API importability and tiny in-memory behavior only.
- A passing data probe proves a resource is discoverable on the current search path, not that a larger corpus workflow is correct.
- Optional backend and external-service capabilities must not be represented as CPU-verified.
- In a proxied environment, downloader `file://` fixture checks may need the explicit trusted-proxy opt-in documented in the troubleshooting reference; do not generalize that opt-in to untrusted downloads.
- If a future NLTK release changes data package IDs, CLI flags, pickle compatibility, or public signatures, refresh the affected sub-skill and rerun the verification plan.
