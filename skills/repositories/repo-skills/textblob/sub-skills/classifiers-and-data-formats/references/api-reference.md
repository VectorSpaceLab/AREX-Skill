# TextBlob classifier and format API reference

This is a distilled operating reference for `textblob.classifiers`,
`textblob.formats`, and blob classification APIs.

## Constructor signatures

| API | Signature | Main use |
| --- | --- | --- |
| `NaiveBayesClassifier` | `(train_set, feature_extractor=basic_extractor, format=None, **kwargs)` | Default text classifier; supports probability and informative features. |
| `DecisionTreeClassifier` | `(train_set, feature_extractor=basic_extractor, format=None, **kwargs)` | Decision-tree classifier with pretty tree and pseudocode output. |
| `MaxEntClassifier` | `(train_set, feature_extractor=basic_extractor, format=None, **kwargs)` | NLTK maximum entropy classifier; can be slow. |
| `PositiveNaiveBayesClassifier` | `(positive_set, unlabeled_set, feature_extractor=contains_extractor, positive_prob_prior=0.5, **kwargs)` | Binary classifier from positive examples plus unlabeled background. |
| `TextBlob` | `(text, tokenizer=None, pos_tagger=None, np_extractor=None, analyzer=None, parser=None, classifier=None, clean_html=False)` | Pass `classifier=cl` to enable `blob.classify()` and sentence classification. |
| `Blobber` | `(tokenizer=None, pos_tagger=None, np_extractor=None, analyzer=None, parser=None, classifier=None)` | Factory for many blobs sharing the same classifier and other model objects. |

`NaiveBayesClassifier`, `DecisionTreeClassifier`, and `MaxEntClassifier` share
`NLTKClassifier` behavior. `PositiveNaiveBayesClassifier` has a different
constructor and update shape.

## Common methods

| Method | Applies to | Return/side effect | Notes |
| --- | --- | --- | --- |
| `classify(text)` | all classifier classes | label | `text` may be a string or token iterable depending on the feature extractor. |
| `accuracy(test_set, format=None)` | `NLTKClassifier` subclasses | `float` | Accepts in-memory pairs or file-like data for standard classifiers. |
| `update(new_data, *args, **kwargs)` | `NaiveBayesClassifier`, `DecisionTreeClassifier`, `MaxEntClassifier` | `True` after retraining | `new_data` is in-memory examples. |
| `labels()` | `NLTKClassifier` subclasses | iterable labels | Useful for validating label normalization. |
| `train(*args, **kwargs)` | `NLTKClassifier` subclasses | underlying NLTK classifier | Called implicitly; call explicitly to pass NLTK training options. |
| `prob_classify(text)` | `NaiveBayesClassifier`, `MaxEntClassifier` | NLTK probability distribution | Use `.max()` and `.prob(label)`. |
| `informative_features(*args, **kwargs)` | `NaiveBayesClassifier` | feature tuple list | Programmatic alternative to printing. |
| `show_informative_features(*args, **kwargs)` | `NaiveBayesClassifier` | prints; returns `None` | Interactive inspection. |
| `pretty_format(*args, **kwargs)` / `pprint(...)` | `DecisionTreeClassifier` | formatted tree string | `pprint` is an alias. |
| `pseudocode(*args, **kwargs)` | `DecisionTreeClassifier` | nested-if pseudocode string | Explanation/audit output. |

## Positive Naive Bayes specifics

```python
from textblob.classifiers import PositiveNaiveBayesClassifier

cl = PositiveNaiveBayesClassifier(
    positive_set=["The team won", "The ball crossed the goal"],
    unlabeled_set=["The president spoke", "The cat slept"],
    positive_prob_prior=0.5,
)
cl.classify("The team controlled the ball")
cl.update(new_positive_data=["The striker scored"], new_unlabeled_data=["A tree fell"])
```

- Positive and unlabeled examples are collections of documents, not
  `(text, label)` pairs.
- The default feature extractor is `contains_extractor(document)`.
- `update(new_positive_data=None, new_unlabeled_data=None, positive_prob_prior=0.5, *args, **kwargs)` appends to the positive/unlabeled sets and retrains.

## `NLTKClassifier` wrapper

Use `NLTKClassifier` by subclassing and setting `nltk_class`:

```python
import nltk
from textblob.classifiers import NLTKClassifier

class MyNaiveBayes(NLTKClassifier):
    nltk_class = nltk.classify.NaiveBayesClassifier
```

If `nltk_class` is missing or `None`, accessing `.classifier`, calling
`.train()`, or calling `.update()` raises `ValueError`.

## Feature extractors

### `basic_extractor(document, train_set)`

Returns features of the form `contains(word): bool` for words from the training
data or supplied training vocabulary. `document` may be a string or token
iterable. If the training set shape is malformed, it can raise
`ValueError("train_set is probably malformed.")`.

### `contains_extractor(document)`

Returns `{f"contains({token})": True, ...}` for tokens present in the document.
It is the default for `PositiveNaiveBayesClassifier`.

### Custom extractor contract

A custom extractor may accept one or two arguments:

```python
def extractor(document): ...
def extractor(document, train_words): ...
```

It must return a dictionary-like feature mapping. TextBlob retries
one-argument extractors automatically after a two-argument call fails with
`TypeError` or `AttributeError`.

## TextBlob classification APIs

| API | Behavior |
| --- | --- |
| `TextBlob(text, classifier=cl)` | Stores the classifier on the blob. |
| `blob.classify()` | Calls `cl.classify(blob.raw)`; raises `NameError` without a classifier. |
| `blob.sentences` | Creates `Sentence` objects sharing the classifier. |
| `sentence.classify()` | Calls the same classifier on the sentence raw string. |
| `Blobber(classifier=cl)` | Creates multiple blobs sharing the classifier object. |

Sentence splitting may require NLTK sentence data even when direct classifier
calls work.

## Format API

| API | Behavior |
| --- | --- |
| `formats.detect(fp, max_read=1024)` | Returns a registered format class for a file-like object or `None`; resets stream position. |
| `formats.get_registry()` | Returns the ordered registry mapping names to classes. Built-ins include `csv`, `json`, and `tsv`. |
| `formats.register(name, format_class)` | Adds or replaces a registry entry. |
| `formats.BaseFormat(fp, **kwargs)` | Interface for custom formats; implement `detect(cls, stream)` and `to_iterable(self)`. |
| `formats.DelimitedFormat` | Base class for delimiter-separated data; set `delimiter`. |
| `formats.CSV` | Comma-delimited `text,label` rows. |
| `formats.TSV` | Tab-delimited `text,label` rows. |
| `formats.JSON` | JSON array of objects with `text` and `label`. |
| `textblob.exceptions.FormatError` | Raised when auto-detection fails for file-like training data. |

`**kwargs` passed to standard classifier constructors are forwarded to the
format class when a file-like training set is read.
