# TextBlob extensions

TextBlob calls reusable custom models and language packages "extensions". Extensions are ordinary installable Python packages that expose TextBlob-compatible classes; TextBlob does not require a special plugin loader for model classes used through constructor injection.

## Naming and imports

Use these conventions for packages intended to be discovered as TextBlob extensions:

| Extension type | Distribution/install name | Python import name | Example shape |
|---|---|---|---|
| Generic model extension | `textblob-name` | `textblob_name` | install `textblob-aptagger`, import `textblob_aptagger` |
| Language extension | `textblob-xx` | `textblob_xx` | `xx` is a two- or three-letter language code |

The most common import failure is confusing hyphens and underscores: package managers install a distribution with a hyphen, Python imports a module with an underscore.

## Model extension structure

A model extension can expose any of these TextBlob-compatible classes:

- `BaseTagger` implementation for `pos_tagger=`.
- `BaseNPExtractor` implementation for `np_extractor=`.
- `BaseTokenizer` or NLTK `TokenizerI` implementation for `tokenizer=`.
- `BaseSentimentAnalyzer` implementation for `analyzer=`.
- `BaseParser` implementation for `parser=`.
- Classifier object with `classify(text)` for `classifier=`; full classifier training/evaluation should follow the classifier sub-skill.
- Optional `textblob.formats.BaseFormat` or `DelimitedFormat` subclass registered with `formats.register(...)` for classifier training data.

Minimal package layout:

```text
textblob-name/
  pyproject.toml
  textblob_name/
    __init__.py
    taggers.py
    tokenizers.py
    sentiments.py
    parsers.py
    np_extractors.py
    formats.py
```

Minimal exported class:

```python
# textblob_name/taggers.py
from textblob.base import BaseTagger

class MyTagger(BaseTagger):
    def tag(self, text, tokenize=True):
        return [(token, "NN") for token in str(text).split()]
```

User code then imports and injects the model explicitly:

```python
from textblob import TextBlob
from textblob_name.taggers import MyTagger

blob = TextBlob("extension text", pos_tagger=MyTagger())
print(blob.tags)
```

## Language extension structure

A language extension follows the same model-interface pattern but groups models and helpers for a language. Package names should be `textblob-xx`, where `xx` is a two- or three-letter language code. Keep language resources package-local and expose constructor-ready model instances/classes:

```python
from textblob import Blobber
from textblob_xx.taggers import LanguageTagger
from textblob_xx.tokenizers import LanguageTokenizer
from textblob_xx.sentiments import LanguageSentimentAnalyzer

tb = Blobber(
    tokenizer=LanguageTokenizer(),
    pos_tagger=LanguageTagger(),
    analyzer=LanguageSentimentAnalyzer(),
)
```

Use a language extension when tokenization, tagging, sentiment, or parsing assumptions differ from TextBlob's English defaults. Do not overload an English default model with hidden language behavior unless the caller explicitly selects it.

## Packaging checklist

- Declare a runtime dependency on `textblob` and any model dependencies needed at import or inference time.
- Keep optional heavy model downloads explicit; avoid downloading resources during module import.
- Export constructor-ready classes from stable modules; avoid requiring users to read package internals.
- Include tests that instantiate each model and pass it to `TextBlob` or `Blobber`.
- Document output shapes, corpus/model resource requirements, and supported Python/TextBlob versions.
- If the extension provides a classifier data format, register it at the point the user opts in; avoid surprising global registry changes on unrelated imports.

## Model resources and state

TextBlob stores model objects on each `TextBlob` or `Blobber` instance. With `Blobber`, every blob created by the factory shares the exact same model object references. That is useful for loaded models, trained analyzers, cached taggers, or deterministic configuration.

Be explicit about state:

- If model objects are immutable or read-only after initialization, `Blobber` sharing is ideal.
- If model objects update counters or mutable caches, sharing may be intended but should be documented.
- If each text must be isolated, construct a new model instance for each `TextBlob` instead of using a shared `Blobber`.

## Classifier format registration cross-link

For data formats, use TextBlob's registry:

```python
from textblob import formats

class PipeDelimitedFormat(formats.DelimitedFormat):
    delimiter = "|"

formats.register("psv", PipeDelimitedFormat)
```

Then a TextBlob classifier can read file-like training data with `format="psv"`. For schema validation, file-like input behavior, classifier methods, and custom feature extractors, route to `../classifiers-and-data-formats/SKILL.md`.

## What not to put in an extension

- Ordinary use of built-in TextBlob models. Route users to `../core-nlp-workflows/SKILL.md`.
- WordNet, spelling, and morphology wrappers unless the extension is specifically about word-level behavior. Route to `../word-and-lexical-tools/SKILL.md`.
- Large model artifacts checked into the package without a clear license and loading story.
- Hidden network downloads at import time or in constructors used by `TextBlob(...)`.
