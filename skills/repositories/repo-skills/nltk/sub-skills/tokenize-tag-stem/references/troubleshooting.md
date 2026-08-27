# Troubleshooting: NLTK Tokenize, Tag, Stem, Lemmatize, Sentiment

Use this guide when a preprocessing workflow fails or returns surprising tokens/tags/stems. Route data package installation details to `data-and-downloader` when the fix requires downloads or path changes.

## Missing data resources

| Symptom/error fragment | Likely missing package | Recovery |
| --- | --- | --- |
| `Resource 'punkt_tab' not found` or attempted `tokenizers/punkt_tab/<language>/` | `punkt_tab` | Download/check `punkt_tab` or call `word_tokenize(..., preserve_line=True)` if sentence splitting is not needed. |
| `averaged_perceptron_tagger_eng` | English POS tagger data | Download/check `averaged_perceptron_tagger_eng`. |
| `averaged_perceptron_tagger_rus` | Russian POS tagger data | Download/check `averaged_perceptron_tagger_rus` and call `pos_tag(..., lang="rus")`. |
| `universal_tagset` or a missing `*.map` | Universal tag mappings | Download/check `universal_tagset`; current Russian universal mapping has compatibility logic for missing `ru-rnc-new.map`. |
| `wordnet` while lemmatizing or using synonyms | WordNet corpus | Download/check `wordnet`; add `omw-2.0` for multilingual WordNet data. |
| `vader_lexicon` | VADER lexicon | Download/check `vader_lexicon`; the default path is `sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt`. |
| Brown/Treebank examples fail | Example corpora | Download/check only the corpus used by the example (`brown`, `treebank`, etc.). |

Always prefer targeted downloads:

```bash
python -m nltk.downloader -d /project/nltk_data punkt_tab averaged_perceptron_tagger_eng
export NLTK_DATA=/project/nltk_data
```

Then re-run a no-download probe before repeating the task.

## `word_tokenize` behaves differently from `WordPunctTokenizer`

NLTK has multiple tokenizers with different goals.

- `word_tokenize` uses Treebank-style tokenization and, by default, Punkt sentence splitting.
- `TreebankWordTokenizer` preserves constructs such as `$3.88` differently from simple punctuation splitting.
- `WordPunctTokenizer` splits punctuation aggressively (`$3.88` -> `['$', '3', '.', '88']`).
- `TweetTokenizer` treats emoticons, handles, URLs, phone numbers, and repeated characters specially.

Fix: choose the tokenizer that matches the downstream contract and write a one-string expected-token assertion. Do not switch tokenizers silently to “fix” a test without explaining the changed token semantics.

## Punkt language and `preserve_line` pitfalls

Symptoms:

- German or other abbreviations split incorrectly.
- CLI uses `--language en` but the installed resource is `english`.
- Missing `punkt_tab` appears even though the task only needs line-level word splitting.

Fixes:

```python
from nltk import word_tokenize
word_tokenize(text, language="english", preserve_line=False)  # needs punkt_tab/english
word_tokenize(text, preserve_line=True)                       # no sentence splitting
```

For CLI:

```bash
printf 'Hello, world!\n' | nltk tokenize --preserve-line
printf 'Dr. Jones left. He returned.\n' | nltk tokenize --language english
```

Use `--preserve-line` when each input line is already a sentence or when no-download behavior is required.

## Regex tokenizer surprises

| Symptom | Cause | Fix |
| --- | --- | --- |
| Output contains only a capture group instead of full matches | Capturing groups in `RegexpTokenizer`/`regexp_tokenize` alter returned tokens. | Use non-capturing groups `(?:...)` unless group-only output is intended. |
| Backreferences behave strangely | Backreferences require capturing groups, which conflict with tokenizer output expectations. | Avoid backreferences in token regexes or post-process with `re.finditer`. |
| Empty strings appear | Gap/token pattern plus `discard_empty=False`. | Set `discard_empty=True` or filter results. |
| Regex is very slow on adversarial input | Catastrophic backtracking. | Simplify nested quantifiers, use bounded repetitions, and test on long strings. |

## Tweet tokenizer edge cases

- `strip_handles=True` removes handles but punctuation adjacent to the handle may remain.
- `reduce_len=True` normalizes repeated characters but does not perform spelling correction.
- `match_phone_numbers=True` can preserve common phone-number forms; set it `False` for identifiers that look like phone numbers but should be split differently.
- `preserve_case=False` lowercases most text; keep it `True` if capitalization is a feature.

Validate with the specific strings the user cares about; social text tokenization is intentionally heuristic.

## POS tagging input and language errors

| Symptom | Cause | Fix |
| --- | --- | --- |
| `TypeError: tokens: expected a list of strings, got a string` | Raw string passed to `pos_tag`. | Tokenize first: `pos_tag(word_tokenize(text, preserve_line=True))`. |
| `NotImplementedError` for language | `lang` is not `"eng"` or `"rus"`, or is `None`. | Use supported language codes or train/configure a custom tagger. |
| Many `None` tags from a trained tagger | N-gram/unigram tagger saw unknown tokens and has no backoff. | Add `RegexpTagger`/`DefaultTagger` backoff or more training data. |
| Universal tags fail | `universal_tagset` missing or unsupported tagset mapping. | Install/check `universal_tagset`; verify the corpus/tagger supports mapping. |
| English tags for non-English text | Default `lang="eng"` applied. | Specify `lang="rus"` where supported, or do not use pretrained `pos_tag` for unsupported languages. |

For batch workloads, prefer `pos_tag_sents` to reusing `pos_tag` in a loop; it reuses the cached tagger.

## Tagger evaluation surprises

- `accuracy(gold_sents)` expects gold tagged sentences and compares against `tagger.tag(untag(sent))` internally.
- If train and test come from the same slice, reported accuracy is inflated.
- OOV tokens reveal the backoff strategy; report `None` tags or backoff tags explicitly.
- `evaluate_per_tag`/`confusion` outputs can be wide; truncate or sort by count for reports.

## Stemming and lemmatization surprises

| Symptom | Cause | Fix |
| --- | --- | --- |
| Porter lowercases output unexpectedly | `PorterStemmer.stem(..., to_lowercase=True)` default. | Pass `to_lowercase=False` when preserving case is required. |
| Different Porter output across examples | Different mode (`NLTK_EXTENSIONS`, `MARTIN_EXTENSIONS`, `ORIGINAL_ALGORITHM`). | State the mode and pin it in code. |
| Snowball ignore-stopwords changes results | `ignore_stopwords=True` preserves some stopwords. | Choose and document `ignore_stopwords`; check language support. |
| Lemmatizer returns the input unchanged | WordNet data missing, wrong POS, or no lemma exists. | Install/check WordNet and pass the correct POS (`n`, `v`, `a`, `r`, `s`). |
| Multilingual WordNet lookups fail | `omw-2.0` missing. | Install/check `omw-2.0` with `wordnet`. |

Stemming is heuristic string reduction; lemmatization is lexicon/morphology-based. Do not compare them as if they should return the same output.

## VADER sentiment failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `LookupError` for VADER lexicon on constructing `SentimentIntensityAnalyzer` | `vader_lexicon` missing. | Install/check `vader_lexicon`. |
| Empty string returns neutral zero scores | Expected behavior. | Treat as valid neutral output, not an error. |
| Scores are sensitive to case/punctuation | VADER intentionally uses capitalization, exclamation, boosters, negation, emoticons, and contrastive conjunctions. | Preserve the original text if those signals matter. |
| User wants trained sentiment classifier, not lexicon rules | VADER is rule/lexicon-based. | Use `SentimentAnalyzer` for feature extraction and route classifier training to `ml-metrics-and-translation`. |

## CLI failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `nltk: command not found` | Console script not on `PATH` or package not installed. | Run via the environment's scripts directory or reinstall NLTK; use the bundled CLI smoke to verify. |
| CLI hangs or waits for input | `nltk tokenize` reads stdin. | Pipe input or redirect a file. |
| `--language` plus no `--preserve-line` raises Punkt LookupError | Sentence splitting requires `punkt_tab`. | Install/check `punkt_tab` or add `--preserve-line`. |
| Parallel mode is slower | `--processes` has overhead for small files. | Use `--processes 1` for short inputs. |
| Progress bar mixes with captured output | The CLI uses tqdm over lines. | Capture stdout/stderr separately or use API tokenization in scripts. |

## Smoke scripts

If a preprocessing workflow fails, first run:

```bash
python /path/to/text_preprocess_smoke.py --json
python /path/to/tokenize_cli_smoke.py --json
```

The API smoke performs no downloads and reports optional data resources as present/missing. If these fail at import time, fix the Python environment before debugging NLTK data or user code.
