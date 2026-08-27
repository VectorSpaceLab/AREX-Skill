# Troubleshooting custom TextBlob models and extensions

Use this reference when custom model injection, extension imports, or shared model workflows fail. Root-level install/corpus issues are handled by the parent skill's setup and troubleshooting references; this file focuses on custom-model symptoms.

## Constructor raises `ValueError`

Symptoms:

- `ValueError: pos_tagger must be an instance of BaseTagger`
- `ValueError: np_extractor must be an instance of BaseNPExtractor`
- `ValueError: analyzer must be an instance of BaseSentimentAnalyzer`
- `ValueError: parser must be an instance of BaseParser`
- `ValueError: tokenizer must be an instance of BaseTokenizer`

Cause:

TextBlob validates most model arguments with `isinstance(...)`. A class that merely has a method named `tag`, `parse`, or `analyze` is not enough for these arguments.

Recovery:

```python
from textblob.base import BaseTagger

class MyTagger(BaseTagger):
    def tag(self, text, tokenize=True):
        return [(token, "NN") for token in str(text).split()]
```

If the user already has a non-inheriting tagger, wrap it:

```python
from textblob.base import BaseTagger

class TaggerAdapter(BaseTagger):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def tag(self, text, tokenize=True):
        return self.wrapped.tag(str(text))
```

Pass an **instance**, not the class: `TextBlob("text", pos_tagger=MyTagger())`, not `pos_tagger=MyTagger`.

Exception: `tokenizer=` also accepts NLTK tokenizer instances that implement NLTK's `TokenizerI`, such as `TabTokenizer`.

## NLTK tokenizer is accepted but another model is rejected

TextBlob intentionally allows NLTK tokenizer instances for `tokenizer=`, but taggers, NP extractors, sentiment analyzers, and parsers must inherit the TextBlob base classes. Do not use NLTK tokenizer acceptance as evidence that other duck-typed objects will work.

## `.tokens`, `.words`, and punctuation do not match expectations

Facts:

- `.tokens` returns the custom tokenizer output directly.
- `.words` uses the custom tokenizer output directly for non-default tokenizers.
- TextBlob's special punctuation-filtering behavior applies to the default `WordTokenizer` path, not arbitrary custom tokenizers.

Recovery:

- If punctuation should be excluded, filter it inside the custom tokenizer.
- If punctuation should be kept for a specific workflow, use `.tokens` and document the token contract.
- If sentence-level behavior is needed, remember that `TextBlob.sentences` uses TextBlob sentence segmentation; custom tokenizers affect the resulting sentences' `.words` and `.tokens`, not the initial sentence split.

## Custom tagger works on `Sentence` but `TextBlob(...).tags` needs corpora

`TextBlob(...).tags` first creates sentence objects, and sentence segmentation may require NLTK sentence data in a normal installation. A pure custom tagger does not necessarily remove that requirement for multi-sentence `TextBlob` tagging.

Recovery options:

- Ensure the parent TextBlob setup/corpus check passes before calling `TextBlob(...).tags`.
- For a no-corpus unit smoke of only the tagger, call `Sentence("text", pos_tagger=tagger).tags`.
- If a workflow must avoid sentence segmentation, call the custom tagger directly or design a wrapper API outside TextBlob's `.tags` property.

## Custom analyzer appears ignored by `.polarity` or `.subjectivity`

Symptoms:

- `blob.sentiment` shows the custom analyzer output, but `blob.polarity` and `blob.subjectivity` are still pattern-based floats.

Cause:

The `.sentiment` property uses `blob.analyzer`. The `.polarity` and `.subjectivity` convenience properties use TextBlob's built-in pattern analyzer directly.

Recovery:

- Read `blob.sentiment` for custom analyzer results.
- If the analyzer returns a namedtuple, access fields on that object.
- Do not use `.polarity`/`.subjectivity` as verification of a custom analyzer.

## `sentiment_assessments` fails with a custom analyzer

`blob.sentiment_assessments` calls `analyzer.analyze(blob.raw, keep_assessments=True)`. If your custom analyzer only accepts one positional argument, this property can fail even though `blob.sentiment` works.

Recovery:

```python
class Analyzer(BaseSentimentAnalyzer):
    def analyze(self, text, keep_assessments=False):
        ...
```

Or accept `**kwargs` and ignore unsupported options.

## Custom analyzer never trains, or trains repeatedly

`BaseSentimentAnalyzer` initializes `_trained = False`. Its `train()` only flips this flag. If the subclass overrides `analyze`, it must either call `train()` lazily or require explicit training before use.

Pattern:

```python
class Analyzer(BaseSentimentAnalyzer):
    def train(self):
        self.model = {"ok": 1}
        super().train()

    def analyze(self, text):
        if not self._trained:
            self.train()
        ...
```

With `Blobber`, one analyzer object is shared across blobs, so lazy training happens once per shared analyzer if implemented correctly.

## Blobber sharing causes state bleed

`Blobber` intentionally shares the same model object references across blobs. This is correct for heavy read-only models and trained analyzers, but surprising for mutable counters, accumulators, or per-document caches.

Recovery:

- For shared trained models: construct once, pass to `Blobber`, and treat it as read-only during inference.
- For per-document state: instantiate separate model objects for each `TextBlob`, or make the model reset state at the beginning of each `tag`, `extract`, `analyze`, or `parse` call.
- To verify sharing, assert `blob1.analyzer is blob2.analyzer` or inspect `repr(Blobber(...))` for model classes.

## Parser output is not in the expected TextBlob format

TextBlob does not validate `BaseParser.parse` output shape. The built-in parser returns a tagged parse string, but a custom parser can return any deterministic representation that downstream code expects.

Recovery:

- Document the output shape beside the parser class.
- If downstream code expects the built-in slash-delimited parse string, return a compatible string from `parse`.
- Use `blob.parse(parser=other_parser)` for one-off parser comparisons without changing the blob's default parser.

## Noun phrase extractor output changes case or loses short phrases

`blob.noun_phrases` lowercases extracted strings and filters out phrases of length 1 after stripping. This is TextBlob behavior, not necessarily the extractor's behavior.

Recovery:

- Return full strings from `extract(text)` and expect lowercase `WordList` output from `blob.noun_phrases`.
- If original case or one-character terms matter, call the extractor directly instead of using `blob.noun_phrases`.

## Extension install succeeds but import fails

Check naming:

- Install/distribution names use hyphens: `textblob-name`.
- Python import names use underscores: `import textblob_name`.
- Language packages use language-code distribution names such as `textblob-xx` and import modules such as `textblob_xx`.

Also confirm the package exports the module path documented by the extension and does not hide model classes behind development-only extras.

## Custom classifier or format fails

Constructor injection does not validate classifier type, but `blob.classify()` calls `classifier.classify(blob.raw)`. Implement that method or use TextBlob's built-in classifiers.

For custom data formats:

- Register the format with `textblob.formats.register(name, FormatClass)`.
- Implement `FormatClass.detect(stream)` and `to_iterable()`.
- Pass a file-like object to classifier constructors when using file formats.

Route schema, training, evaluation, updates, feature extractors, and `FormatError` debugging to `../classifiers-and-data-formats/SKILL.md`.

## Safe local smoke

Run the bundled smoke from any directory in an environment where `textblob` is installed:

```bash
python scripts/custom_model_smoke.py --json
```

It does not download corpora or write data files. It validates custom tokenizer/tagger/analyzer/parser/NP extractor integration, shared `Blobber` model identity, and rejection of an invalid tagger.
