---
name: tokenize-tag-stem
description: "Use NLTK tokenization, detokenization, POS tagging, tagger
  training, stemming, lemmatization, and sentiment preprocessing APIs without
  reopening the source repo."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tokenize Tag Stem

Use this sub-skill when the task is about NLTK text preprocessing: tokenizing or detokenizing strings, running the `nltk tokenize` CLI, POS-tagging tokens, training simple taggers, stemming or lemmatizing words, or using VADER/basic sentiment preprocessing.

Route away from this sub-skill when the task is mainly about:

- Installing, locating, or repairing NLTK data packages: use [`../data-and-downloader/SKILL.md`](../data-and-downloader/SKILL.md).
- Grammars, parse trees, chunkers, dependency graphs, semantics, or theorem-proving: use [`../grammar-parse-semantics/SKILL.md`](../grammar-parse-semantics/SKILL.md).
- Classifiers, language models, probability distributions, metrics, or translation/alignment algorithms after features are prepared: use [`../ml-metrics-and-translation/SKILL.md`](../ml-metrics-and-translation/SKILL.md).

## Fast Paths

- For no-download word splitting, prefer `WordPunctTokenizer`, `TreebankWordTokenizer`, `TweetTokenizer`, or `word_tokenize(text, preserve_line=True)`. `sent_tokenize()` and `word_tokenize(..., preserve_line=False)` need Punkt table data for the selected language.
- For command-line tokenization, use `nltk tokenize`; it reads stdin and exposes `--language`, `--preserve-line`, `--processes`, `--encoding`, and `--delimiter`. The bundled CLI smoke checks the installed console script.
- For tweets/social text, use `TweetTokenizer(strip_handles=True, reduce_len=True, preserve_case=...)`; decide whether phone numbers should be matched with `match_phone_numbers`.
- For POS tags, pass a list of tokens to `pos_tag(tokens, tagset=None, lang="eng")` or a list of token lists to `pos_tag_sents`. English uses `averaged_perceptron_tagger_eng`; Russian uses `lang="rus"` and `averaged_perceptron_tagger_rus`.
- For a quick custom baseline tagger, combine `RegexpTagger` rules with `UnigramTagger(train_sents, backoff=...)`; evaluate with `accuracy`, `evaluate_per_tag`, or a `ConfusionMatrix` when gold tagged sentences are available.
- For stemming, use `PorterStemmer(mode=...)`, `SnowballStemmer(language, ignore_stopwords=False)`, `LancasterStemmer`, `RegexpStemmer`, or language-specific stemmers. Porter and most Snowball workflows do not need NLTK data.
- For lemmatization, `WordNetLemmatizer.lemmatize(word, pos="n")` depends on WordNet for real morphology; download/check `wordnet` and `omw-2.0` when multilingual or synonym-aware behavior is needed.
- For sentiment, `SentimentIntensityAnalyzer()` requires `vader_lexicon`; route missing lexicon errors to the data/downloader sub-skill. `SentimentAnalyzer` can build features for a classifier workflow, which then routes to the ML sub-skill.

## Reference Map

- Public tokenization, tagging, stemming, lemmatization, and sentiment API contracts plus data-package requirements: [`references/api-reference.md`](references/api-reference.md).
- Task recipes for tokenizer selection, CLI use, POS tagging, tagger baselines, stemming/lemmatization, and sentiment preprocessing: [`references/workflows.md`](references/workflows.md).
- Diagnosis for missing `punkt_tab`, perceptron taggers, universal tagsets, VADER/WordNet data, regex pitfalls, language codes, and CLI/API misuse: [`references/troubleshooting.md`](references/troubleshooting.md).
- Console-script check for `nltk tokenize` with tiny stdin: [`scripts/tokenize_cli_smoke.py`](scripts/tokenize_cli_smoke.py).
- No-download API smoke for tokenizer/stemmer basics plus optional data-resource probes: [`scripts/text_preprocess_smoke.py`](scripts/text_preprocess_smoke.py).

## Minimum Validation Pattern

1. Print `nltk.__version__`, the exact API or CLI route, and whether the workflow is allowed to download NLTK data.
2. For tokenization, test one representative string and state whether sentence splitting is enabled (`preserve_line=False`) or skipped (`preserve_line=True`).
3. For POS tagging, assert the input is `list[str]`, not a raw string; for batches, assert `list[list[str]]`.
4. Before running data-backed APIs, probe exact resources such as `tokenizers/punkt_tab/english/`, `taggers/averaged_perceptron_tagger_eng/`, `taggers/universal_tagset/`, `corpora/wordnet/`, or `sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt`.
5. For custom taggers, keep training/testing data separated and report unknown-token behavior instead of hiding `None` tags.
6. Run the bundled no-download smoke from any current working directory in an environment with NLTK installed:

```bash
python /path/to/skills/disco/nltk/sub-skills/tokenize-tag-stem/scripts/text_preprocess_smoke.py --json
python /path/to/skills/disco/nltk/sub-skills/tokenize-tag-stem/scripts/tokenize_cli_smoke.py --json
```
