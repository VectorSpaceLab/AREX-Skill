# NLTK Cross-Cutting Troubleshooting

Use this reference when a task fails before one sub-skill can complete. Keep the exact error, attempted resource path, input shape, NLTK version, and selected sub-skill visible.

## Install/import problems

- `ModuleNotFoundError: nltk`: install the `nltk` distribution into the Python that will run the task; verify with `python -c "import nltk; print(nltk.__version__)"`.
- `nltk` command not found: the console script directory is not on `PATH`; run the environment's script directly or reinstall into the active environment.
- Import works but an optional module fails: install only the documented extra or external dependency. Base NLTK does not include `numpy`, `scikit-learn`, `scipy`, `python-crfsuite`, `matplotlib`, `twython`, or Java tools.
- A source checkout masks an installed distribution: verify the environment from a directory outside the checkout and use the intended Python executable.
- Version drift: check `nltk.__version__` and consult [`repo-provenance.md`](repo-provenance.md) before relying on resource names or pickle compatibility behavior.

## Data and model lookup

A `LookupError` is usually a missing NLTK data package, not a broken Python import.

1. Copy the attempted resource path from the exception.
2. Print `NLTK_DATA` and `nltk.data.path`.
3. Probe the exact resource with `nltk.data.find()` or the data sub-skill checker.
4. Download only the required package into a controlled top-level `nltk_data` directory.
5. Re-run the probe before the NLP operation.

Common mappings:

| Failing operation | Targeted package |
| --- | --- |
| `sent_tokenize` or default `word_tokenize` | `punkt_tab` |
| English `pos_tag` | `averaged_perceptron_tagger_eng` |
| Russian `pos_tag(lang="rus")` | `averaged_perceptron_tagger_rus` |
| `tagset="universal"` | `universal_tagset` |
| WordNet/lemmatization | `wordnet`, optionally `omw-2.0` |
| VADER | `vader_lexicon` |
| corpus-backed examples | the named corpus, such as `brown`, `treebank`, `reuters`, or `comtrans` |

Do not recommend `all`, `all-corpora`, or `popular` as the first fix. They are broad, slow, and make reproducibility harder.

## Path and cache errors

- Keep `NLTK_DATA` pointed at the top-level data directory, not `corpora/`, `taggers/`, or a single package.
- If `NLTK_DATA` changes after `import nltk.data`, update `nltk.data.path` in the current process or restart Python.
- Earlier `nltk.data.path` entries take precedence; remove stale directories or prepend the intended project directory.
- Use `nltk.data.clear_cache()` or `cache=False` after intentionally changing a local resource.
- `nltk.data.find()` uses POSIX-style resource names and can look inside `.zip` packages; directory probes inside archives need a trailing slash.

## API-shape failures

- `pos_tag` expects `list[str]`, not a raw string; use a tokenizer first.
- `RegexpParser` expects POS-tagged `(word, tag)` tuples, not raw text.
- CFG/chart parsers expect already tokenized strings and a grammar whose terminals cover every token.
- NLTK classifiers expect `[(featureset_dict, label), ...]`; predictions receive a feature dictionary, not raw text.
- N-gram LMs expect tokenized sentences and n-gram tuples; `padded_everygram_pipeline` returns consumable iterators.
- Translation metrics expect tokenized references/hypotheses; `AlignedSent` indexes are zero-based and the two index dimensions have a defined direction.

## Optional dependencies and external tools

Install only when the task requires them:

- `machine_learning`: `numpy`, `python-crfsuite`, `scikit-learn`, `scipy`.
- `plot`: `matplotlib` and often a display/backend for GUI plots.
- `tgrep`: `pyparsing`.
- `twitter`: `twython` plus credentials/network when using Twitter APIs.
- `corenlp`: `requests` plus a running Stanford CoreNLP service and models.
- Stanford, Senna, Malt, BLLIP, Prover9, Mace4, Weka, MEGAM, and TADM wrappers require external binaries, Java, services, or model paths. They are not proven by `import nltk` or a CPU-only smoke.

When a task can use a pure-Python alternative, prefer `NaiveBayesClassifier`, a small `RegexpTagger`, an in-memory CFG, or base translation metrics before adding an external backend.

## Security and untrusted data

Treat path, archive, XML, and pickle errors as security signals:

- `Unsafe resource path`, traversal, encoded traversal, absolute-path, or pathsec rejection: stop and inspect the resource name; do not bypass with a different protocol.
- Zip Slip, symlink escape, null-byte, cross-package overwrite, checksum, or size mismatch: discard the suspect package and retry from a trusted NLTK index into a controlled directory.
- XML entity-expansion errors: do not disable safe parsing or accept the index as-is.
- `pathsec.urlopen` refuses a proxied `file://` or other fetch during downloader tests: the active proxy makes SSRF protection impossible to guarantee. If and only if the proxy is trusted and the task explicitly requires that path, opt in with `NLTK_ALLOW_PROXIED_URLOPEN=1` or `nltk.pathsec.ALLOW_PROXIED_FETCH=True`; otherwise keep the test offline or use a different controlled fixture.
- Legacy pickle loading errors: use current high-level APIs and pickle-free resource packages such as `punkt_tab` and language-specific perceptron taggers; do not disable restrictions for untrusted data.

## Escalation

If the exact resource is present, the input shape is valid, base imports and the sub-skill smoke pass, and the failure still reproduces, reduce it to a tiny no-download fixture. Only then investigate optional backends, large corpora, network mirrors, or external services.
