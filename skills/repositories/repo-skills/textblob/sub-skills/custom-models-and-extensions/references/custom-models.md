# Custom model contracts

This reference distills TextBlob's model-extension surface. Generated code should import public TextBlob modules such as `textblob.base`, `textblob.blob`, `textblob.tokenizers`, `textblob.taggers`, `textblob.np_extractors`, `textblob.sentiments`, `textblob.parsers`, `textblob.classifiers`, and `textblob.formats` from the installed package.

## Constructor insertion points

`TextBlob` accepts model instances at construction time:

```python
from textblob import TextBlob

blob = TextBlob(
    "model-driven text",
    tokenizer=my_tokenizer,
    pos_tagger=my_tagger,
    np_extractor=my_np_extractor,
    analyzer=my_sentiment_analyzer,
    parser=my_parser,
    classifier=my_classifier,
)
```

`Blobber` accepts the same model objects, except it has no `text` argument and no `clean_html` option:

```python
from textblob import Blobber

tb = Blobber(tokenizer=my_tokenizer, analyzer=my_analyzer)
blob_a = tb("first text")
blob_b = tb("second text")
assert blob_a.tokenizer is blob_b.tokenizer
assert blob_a.analyzer is blob_b.analyzer
```

Use `Blobber` when model construction or training is expensive, when model state should be shared deliberately, or when a workflow needs consistent custom behavior across many texts. Use direct `TextBlob(...)` injection for one-off experiments or when each blob should receive a separate model object.

## Validation behavior

TextBlob validates most model constructor arguments before assignment:

| Argument | Must be instance of | Failure |
|---|---|---|
| `tokenizer` | `textblob.base.BaseTokenizer` **or** `nltk.tokenize.api.TokenizerI` | `ValueError` |
| `pos_tagger` | `textblob.base.BaseTagger` | `ValueError` |
| `np_extractor` | `textblob.base.BaseNPExtractor` | `ValueError` |
| `analyzer` | `textblob.base.BaseSentimentAnalyzer` | `ValueError` |
| `parser` | `textblob.base.BaseParser` | `ValueError` |
| `classifier` | not base-class validated at construction | method errors later if incompatible |

`None` means "use TextBlob's default model". Passing a class object instead of an instance fails for validated arguments. NLTK tokenizer instances such as `TabTokenizer`, `BlanklineTokenizer`, `WordPunctTokenizer`, and other `TokenizerI` implementations are valid tokenizers even if they do not inherit `BaseTokenizer`.

## BaseTokenizer

Subclass `BaseTokenizer` when you want a TextBlob-native tokenizer. It inherits NLTK's tokenizer interface and supplies `itokenize` by delegating to `tokenize`.

Contract:

```python
from textblob.base import BaseTokenizer

class PipeTokenizer(BaseTokenizer):
    def tokenize(self, text):
        return [part.strip() for part in str(text).split("|") if part.strip()]

    # itokenize is inherited and yields from tokenize(text, *args, **kwargs)
```

Where it is used:

- `blob.tokens` returns `WordList(blob.tokenizer.tokenize(blob.raw))`.
- `blob.tokenize()` calls the blob tokenizer by default; `blob.tokenize(other_tokenizer)` uses the supplied tokenizer.
- `blob.words` uses the custom tokenizer output directly. Only the default `WordTokenizer` receives TextBlob's historical punctuation-removal path.
- Sentence splitting for `TextBlob.sentences` uses TextBlob's sentence tokenizer, not the custom word tokenizer. Sentence objects still receive the custom tokenizer for their own `.words` and `.tokens`.

Design notes:

- Return a finite list or list-like sequence of strings from `tokenize`.
- Keep side effects out of `tokenize`; it is often called lazily through cached properties.
- Decide whether punctuation should be kept, removed, or normalized; TextBlob will not filter punctuation for arbitrary custom tokenizers.

## BaseTagger

Subclass `BaseTagger` for POS tagging.

Contract:

```python
from textblob.base import BaseTagger

class UpperNounTagger(BaseTagger):
    def tag(self, text, tokenize=True):
        tokens = str(text).split() if tokenize else list(text)
        return [(token, "NNP" if token[:1].isupper() else "NN") for token in tokens]
```

Where it is used:

- `Sentence(..., pos_tagger=tagger).tags` calls `tagger.tag(self)` on a `Sentence` instance, then wraps returned words as `Word` objects.
- `TextBlob(...).tags` flattens sentence-level tags; this can invoke sentence tokenization before tagger calls.

Design notes:

- Accept `text` as either a string-like object or a TextBlob/Sentence-like object; `str(text)` is usually safest.
- Return a list of `(word, tag)` pairs.
- The optional `tokenize=True` parameter is part of the public base signature; include it even when ignored so your tagger remains compatible with callers.
- If the tagger needs a custom tokenizer, either compose the tokenizer inside the tagger or pass both tokenizer and tagger to `TextBlob`/`Blobber`.

## BaseNPExtractor

Subclass `BaseNPExtractor` for noun phrase extraction.

Contract:

```python
from textblob.base import BaseNPExtractor

class CapitalizedNPExtractor(BaseNPExtractor):
    def extract(self, text):
        return [token for token in str(text).split() if token[:1].isupper()]
```

Where it is used:

- `blob.noun_phrases` calls `np_extractor.extract(blob.raw)`.
- TextBlob strips each returned phrase, lowercases it, filters out length-1 phrases, and returns a `WordList`.

Design notes:

- Return strings, not `(phrase, score)` tuples.
- Preserve multiword phrase spacing if downstream counts or display need it.
- Do not expect TextBlob to retain original case in `noun_phrases`; output is normalized to lowercase.

## BaseSentimentAnalyzer

Subclass `BaseSentimentAnalyzer` for sentiment or other text-level analysis exposed through `.sentiment`.

Contract:

```python
from collections import namedtuple
from textblob.base import BaseSentimentAnalyzer

Score = namedtuple("Score", "polarity subjectivity")

class KeywordAnalyzer(BaseSentimentAnalyzer):
    kind = "co"  # continuous; TextBlob also exposes "ds" for discrete analyzers

    def train(self):
        # Optional expensive setup. Base class sets self._trained = True.
        self.lexicon = {"great": 1.0, "bad": -1.0}
        super().train()

    def analyze(self, text):
        if not self._trained:
            self.train()
        words = str(text).lower().split()
        polarity = sum(self.lexicon.get(w.strip(".,!"), 0.0) for w in words)
        return Score(max(-1.0, min(1.0, polarity)), 0.5)
```

Where it is used:

- `blob.sentiment` returns `analyzer.analyze(blob.raw)`.
- `blob.sentiment_assessments` calls `analyzer.analyze(blob.raw, keep_assessments=True)`. If your analyzer should support this property, accept `**kwargs` or a `keep_assessments=False` parameter.
- `blob.polarity` and `blob.subjectivity` are convenience properties backed by TextBlob's built-in pattern analyzer, not by a custom analyzer. Use `blob.sentiment` for custom analyzer output.

Design notes:

- The base `train` method only marks `_trained`; subclasses must store any learned resources themselves.
- Keep output shape documented. Built-in analyzers return namedtuples, but the base contract allows tuple, float, dict, or another object.
- Train lazily inside `analyze` when setup is expensive, or train explicitly before passing the analyzer to `Blobber`.

## BaseParser

Subclass `BaseParser` when implementing `blob.parse()`.

Contract:

```python
from textblob.base import BaseParser

class SlashParser(BaseParser):
    def parse(self, text):
        return " ".join(f"{token}/TOK" for token in str(text).split())
```

Where it is used:

- `blob.parse()` calls `blob.parser.parse(blob.raw)`.
- `blob.parse(other_parser)` uses the supplied parser for that call only.

Design notes:

- Return the representation your workflow expects; the built-in pattern parser returns a tagged parse string.
- Keep parser output deterministic if it will be consumed by tests or by another agent.

## Classifier object injection

`TextBlob(..., classifier=classifier)` and `Blobber(classifier=classifier)` do not validate a classifier base class. The workflow later calls methods on the object:

- `blob.classify()` calls `classifier.classify(blob.raw)`.
- Sentence-level `s.classify()` uses the same classifier object shared from the parent blob.

For training, evaluation, updating, feature extractors, probability APIs, and file-format details, route to `../classifiers-and-data-formats/SKILL.md`.

## Custom data format registration cross-link

TextBlob's classifier format registry lives in `textblob.formats`. A custom format class implements `detect(stream)` and `to_iterable()`, then is registered with `formats.register(name, FormatClass)`.

Minimal shape:

```python
from textblob import formats

class PipeDelimitedFormat(formats.DelimitedFormat):
    delimiter = "|"

formats.register("psv", PipeDelimitedFormat)
```

Once registered, classifier constructors can use `format="psv"` with a file-like object. Treat this as a classifier/data-format workflow and route detailed schema or training questions to `../classifiers-and-data-formats/SKILL.md`.

## Minimal adapter for a non-inheriting tagger

A duck-typed object with `tag()` is not accepted as `pos_tagger`; subclass `BaseTagger` or wrap the object:

```python
from textblob.base import BaseTagger

class ExistingTaggerAdapter(BaseTagger):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def tag(self, text, tokenize=True):
        return self.wrapped.tag(str(text))
```

Use this recovery when a user reports that their tagger "has the right method" but TextBlob still raises `ValueError`.
