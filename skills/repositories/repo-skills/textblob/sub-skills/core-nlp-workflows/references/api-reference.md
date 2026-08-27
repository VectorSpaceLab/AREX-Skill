# TextBlob core NLP API reference

This reference covers the document-level APIs used for ordinary TextBlob work.
It is based on source inspection plus installed-package signature verification.

## Constructors and shared objects

| API | Signature | Notes |
| --- | --- | --- |
| `TextBlob` | `TextBlob(text, tokenizer=None, pos_tagger=None, np_extractor=None, analyzer=None, parser=None, classifier=None, clean_html=False)` | Main document wrapper. Validates most injected models. `clean_html` is deprecated and raises `NotImplementedError`. |
| `Sentence` | `Sentence(sentence, start_index=0, end_index=None, *args, **kwargs)` | Sentence wrapper used by `TextBlob.sentences`. Carries start/end indices and shares parent models. |
| `Blobber` | `Blobber(tokenizer=None, pos_tagger=None, np_extractor=None, analyzer=None, parser=None, classifier=None)` | Factory that reuses the same model objects across blobs. |

Default model objects on `BaseBlob`/`Blobber`:

- `tokenizer`: `WordTokenizer()`
- `pos_tagger`: `NLTKTagger()`
- `np_extractor`: `FastNPExtractor()`
- `analyzer`: `PatternAnalyzer()`
- `parser`: `PatternParser()`

## Core properties and methods

| API | Behavior |
| --- | --- |
| `blob.words` | `WordList` of word tokens without punctuation for the default tokenizer path. |
| `blob.tokens` | `WordList` of tokenizer output, including punctuation when the tokenizer returns it. |
| `blob.tokenize(tokenizer=None)` | Returns a `WordList` using the supplied tokenizer or the blob's default tokenizer. |
| `blob.sentences` | List of `Sentence` objects created from sentence tokenization. |
| `blob.raw_sentences` | Raw string sentences. |
| `blob.serialized` | List of sentence `.dict` values. |
| `blob.to_json(*args, **kwargs)` / `blob.json` | JSON serialization of sentence dictionaries. |
| `blob.parse(parser=None)` | Parse string from the supplied parser or default parser. |
| `blob.classify()` | Calls `classifier.classify(blob.raw)`; raises `NameError` if no classifier exists. |
| `blob.sentiment` | Uses `blob.analyzer.analyze(blob.raw)`. |
| `blob.sentiment_assessments` | Calls `analyzer.analyze(blob.raw, keep_assessments=True)` when supported. |
| `blob.polarity` / `blob.subjectivity` | Convenience properties backed by the built-in `PatternAnalyzer`, not by a custom analyzer. |
| `blob.noun_phrases` | Lowercased `WordList` of extracted phrases with length > 1. |
| `blob.pos_tags` / `blob.tags` | Flattened POS-tag tuples across sentences. |
| `blob.word_counts` | Lowercased word-frequency dictionary. |
| `blob.np_counts` | Noun-phrase frequency dictionary. |
| `blob.ngrams(n=3)` | List of `WordList` n-grams; returns `[]` for `n <= 0`. |
| `blob.correct()` | Returns a new blob with each token spell-corrected. |
| `blob.split(sep=None, maxsplit=sys.maxsize)` | String-like split returning `WordList`. |

## Sentence behavior

`Sentence` objects inherit the same base methods as `TextBlob` but represent a
single sentence. Their `.dict` property contains:

- `raw`
- `start_index`
- `end_index`
- `stripped`
- `noun_phrases`
- `polarity`
- `subjectivity`

`TextBlob.sentences` creates `Sentence` objects that share the parent blob's
model instances, which matters when using `Blobber` or custom models.

## Tokenizer and tagger details

| API | Verified behavior |
| --- | --- |
| `WordTokenizer.tokenize(text, include_punc=True)` | Returns NLTK tokenization; when `include_punc=False`, punctuation is stripped except contraction fragments like `"'s"` or `"n't"`. |
| `SentenceTokenizer.tokenize(text)` | Returns NLTK sentence tokenization and requires NLTK sentence data. |
| `word_tokenize(text, include_punc=True)` | Tokenizes sentences first, then words. Returns a generator. |
| `sent_tokenize(text)` | Returns a generator over sentence strings. |
| `PatternTagger.tag(text, tokenize=True)` | Uses `textblob.en.tag` on string-like input. |
| `NLTKTagger.tag(text)` | Converts strings to `TextBlob` and calls `nltk.tag.pos_tag(text.tokens)`. Requires NLTK corpus data and numpy for the test surface. |

## Sentiment and parsing details

| API | Verified behavior |
| --- | --- |
| `PatternAnalyzer.analyze(text, keep_assessments=False)` | Returns a `Sentiment(polarity, subjectivity)` namedtuple; with `keep_assessments=True`, returns `Sentiment(polarity, subjectivity, assessments)`. |
| `NaiveBayesAnalyzer()` | Discrete sentiment analyzer trained on `movie_reviews`. Returns `Sentiment(classification, p_pos, p_neg)`. |
| `PatternParser.parse(text)` | Returns the pattern-style slash-delimited parse string. |

## Validation behavior

TextBlob validates injected model objects with `isinstance` checks:

- `tokenizer`: `BaseTokenizer` or NLTK `TokenizerI`
- `pos_tagger`: `BaseTagger`
- `np_extractor`: `BaseNPExtractor`
- `analyzer`: `BaseSentimentAnalyzer`
- `parser`: `BaseParser`

Passing a class instead of an instance fails. A custom `classifier` is not
validated at construction time, but it must support `.classify(text)` when used.

## Practical notes

- `.words` and `.tokens` are not the same thing; choose according to whether
  punctuation should be preserved.
- `.sentences` can require corpus data even when plain `TextBlob` import works.
- `.polarity` and `.subjectivity` are convenience accessors for the built-in
  pattern analyzer; use `.sentiment` to read a custom analyzer's output.
- Use `Blobber` for shared model identity across many blobs; use direct
  `TextBlob(...)` when each blob should get a separate model object.
