# Troubleshooting TextBlob core NLP workflows

Use this guide for document-level TextBlob failures: tokenization, sentence
splitting, POS tags, noun phrases, sentiment, parsing, counts, JSON, and
`Blobber` model selection. WordNet/spelling/morphology and classifier training
have separate sibling troubleshooting references.

## Quick triage

1. Run a read-only smoke check in the target environment:

   ```bash
   python scripts/core_nlp_smoke.py --json
   python scripts/core_nlp_smoke.py --skip-corpus-heavy
   ```

2. If corpus-backed checks fail, use the parent setup reference and run the
   explicit TextBlob corpus command in the environment where TextBlob is
   installed:

   ```bash
   python -m textblob.download_corpora lite
   # or, for ConllExtractor and NaiveBayesAnalyzer:
   python -m textblob.download_corpora
   ```

3. Separate property behavior before changing code: `.tokens`, `.words`,
   `.sentences`, `.tags`, `.noun_phrases`, `.sentiment`, `.polarity`, and
   `.subjectivity` do not all use the same models.

## `MissingCorpusError` or NLTK `LookupError`

### Symptoms

- `.sentences`, `.words`, `.tags`, or `SentenceTokenizer` complains about
  missing `punkt_tab`.
- `.tags` with the default tagger complains about
  `averaged_perceptron_tagger_eng`.
- `.noun_phrases` with the default extractor complains about `brown`.
- `ConllExtractor` complains about `conll2000`.
- `NaiveBayesAnalyzer` complains about `movie_reviews`.

### Cause

TextBlob package import does not install NLTK corpora. TextBlob wraps NLTK
lookup errors into a TextBlob missing corpus error for many corpus-backed APIs.

### Recovery

- For default workflows, run:

  ```bash
  python -m textblob.download_corpora lite
  ```

- For optional `ConllExtractor` or `NaiveBayesAnalyzer`, run:

  ```bash
  python -m textblob.download_corpora
  ```

- Re-run `python scripts/core_nlp_smoke.py --json` and confirm sentence, tag,
  and noun phrase checks pass.
- Do not call download commands inside library code that should be deterministic
  or offline; make corpus setup an explicit environment step.

## `.tokens` and `.words` disagree

### Symptom

`.tokens` includes punctuation but `.words` omits punctuation, or a custom
tokenizer causes `.words` to keep punctuation unexpectedly.

### Cause

The default `WordTokenizer` path strips punctuation for `.words`. Custom
tokenizers own their output and TextBlob does not apply the same punctuation
filter to arbitrary tokenizers.

### Recovery

- Use `.tokens` when punctuation is required.
- Use `.words` with the default tokenizer when punctuation should be ignored.
- If a custom tokenizer is required, filter punctuation inside the tokenizer or
  explicitly post-process the `WordList`.
- Record the token contract in downstream data so counts and n-grams are
  reproducible.

## `.polarity` ignores a custom or Naive Bayes analyzer

### Symptom

`TextBlob(text, analyzer=NaiveBayesAnalyzer()).sentiment` returns a discrete
classification, but `.polarity` and `.subjectivity` return pattern-style floats.

### Cause

`.sentiment` uses the configured analyzer. `.polarity` and `.subjectivity` are
convenience properties that call TextBlob's built-in `PatternAnalyzer`.

### Recovery

- Use `.sentiment` for configured analyzer output.
- Only use `.polarity`/`.subjectivity` for the built-in pattern analyzer
  convenience path.
- If a custom analyzer must support assessments, implement
  `analyze(text, keep_assessments=False)` or accept `**kwargs`.

## `blob.classify()` raises `NameError`

### Symptom

`NameError: This blob has no classifier. Train one first!`

### Cause

`TextBlob.classify()` is only available when a classifier object was passed via
`TextBlob(text, classifier=cl)` or `Blobber(classifier=cl)`.

### Recovery

Route to `../classifiers-and-data-formats/SKILL.md`, train a classifier, then
construct the blob with `classifier=cl`.

## `clean_html=True` no longer works

### Symptom

`TextBlob(text, clean_html=True)` raises `NotImplementedError`.

### Cause

The `clean_html` parameter is deprecated. TextBlob intentionally tells callers
to remove HTML markup outside TextBlob.

### Recovery

Strip HTML before constructing the blob, for example with BeautifulSoup's
`get_text()` when that dependency is acceptable, then pass plain text into
`TextBlob`.

## Noun phrases are lowercase or one-character phrases disappear

### Symptom

A custom extractor returns capitalized or short phrases, but `blob.noun_phrases`
contains lowercase phrases and omits length-1 entries.

### Cause

TextBlob strips and lowercases extracted phrases and filters out phrases whose
length is not greater than one.

### Recovery

- Use `blob.noun_phrases` for normalized TextBlob-style noun phrases.
- Call a custom extractor directly if original case or one-character terms are
  meaningful.
- Document whether downstream counts are based on TextBlob-normalized phrases
  or raw extractor output.

## POS tags are slow on the first call

### Symptom

The first `.tags` or `.noun_phrases` call is noticeably slower than subsequent
calls.

### Cause

Several properties are cached and some extractors/taggers lazily train or load
corpus data on first use.

### Recovery

- Warm up with a tiny representative text before timing a workflow.
- Reuse `Blobber` or model instances when many blobs use the same models.
- Do not benchmark first-call corpus loading as steady-state NLP performance.

## Sentence boundaries around unusual punctuation are surprising

### Symptom

Multiple exclamation/question marks or ellipses produce unexpected sentence
splits.

### Cause

Sentence splitting delegates to NLTK's sentence tokenizer. The upstream tests
record multiple-punctuation tokenization as a known skipped edge case.

### Recovery

- Validate sentence boundaries for the target text style before relying on
  indices or sentence-level classification.
- Use a custom sentence preprocessing step or tokenizer outside TextBlob when
  exact punctuation boundary behavior is critical.
- Keep `sentence.start_index` and `sentence.end_index` in outputs so boundary
  decisions are auditable.

## Parser output is not a tree

### Symptom

`blob.parse()` returns a slash-delimited string instead of an object tree.

### Cause

TextBlob's default parser uses a pattern-style parser that returns a tagged
parse string.

### Recovery

- Treat parse output as a string format and document expected columns/tags.
- Use `blob.parse(parser=custom_parser)` only when a custom parser's output
  shape is understood by downstream code.
- Route custom parser implementation to `../custom-models-and-extensions/SKILL.md`.
