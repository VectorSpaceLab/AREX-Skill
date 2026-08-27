# TextBlob classifier workflows

This reference distills TextBlob classifier tasks into operating recipes. The
examples are self-contained and assume `textblob` is installed.

## 1. Pick the classifier

| Need | Use | Notes |
| --- | --- | --- |
| General small text classifier | `NaiveBayesClassifier` | Best default; supports probabilities and informative feature inspection. |
| Human-readable tree or rules | `DecisionTreeClassifier` | Supports `pretty_format()`, `pprint()`, and `pseudocode()`. Can overfit tiny data. |
| Maximum entropy / logistic-style NLTK classifier | `MaxEntClassifier` | Can be slower; keep iterations bounded for smoke tests. |
| Positive-only labeled examples plus unlabeled background | `PositiveNaiveBayesClassifier` | Binary positive/unlabeled workflow. Does not use CSV/JSON/TSV constructor parsing. |
| Wrap another NLTK classifier | subclass of `NLTKClassifier` | Set `nltk_class`; base interface and extension packaging route to the custom-model sub-skill. |

## 2. Train from in-memory examples

```python
from textblob.classifiers import NaiveBayesClassifier

train = [
    ("I love this sandwich", "pos"),
    ("This view is amazing", "pos"),
    ("I do not like this car", "neg"),
    ("This view is horrible", "neg"),
]
test = [("the sandwich was amazing", "pos"), ("the car was horrible", "neg")]

cl = NaiveBayesClassifier(train)
print(cl.classify("amazing sandwich"))
print(cl.accuracy(test))
print(sorted(cl.labels()))
```

A document can be a string or a token iterable:

```python
token_train = [(["bright", "happy"], "pos"), (["awful", "dull"], "neg")]
cl = NaiveBayesClassifier(token_train)
print(cl.classify(["bright", "happy"]))
```

Token-list training is useful when a workflow already has domain-specific
tokenization or must avoid TextBlob/NLTK tokenization during feature extraction.

## 3. Train from CSV, JSON, or TSV

Open files yourself and pass file objects:

```python
from textblob.classifiers import NaiveBayesClassifier

with open("train.json", encoding="utf-8") as fp:
    cl = NaiveBayesClassifier(fp, format="json")

with open("heldout.csv", encoding="utf-8", newline="") as fp:
    print(cl.accuracy(fp, format="csv"))
```

When `format` is omitted, TextBlob samples the file-like object and tries the
registered formats. Use explicit `format=` for large JSON, short ambiguous
files, or production workflows.

See [data formats](data-formats.md) for exact schemas and custom format
registration.

## 4. Classify text and probabilities

```python
label = cl.classify("This library is useful")
prob = cl.prob_classify("This one is a doozy")
print(prob.max())
print(prob.prob("pos"))
```

`prob_classify()` is available on `NaiveBayesClassifier` and
`MaxEntClassifier`. Decision Tree and Positive Naive Bayes still classify with
`classify()`; use `accuracy()` for held-out validation.

## 5. Update with new examples

`update()` retrains the underlying NLTK classifier and returns `True`.

```python
new_data = [("She is my best friend", "pos"), ("He is my sworn enemy", "neg")]
cl.update(new_data)
```

If update examples are stored in a file, parse and validate them first:

```python
from textblob import formats

with open("new_examples.tsv", encoding="utf-8", newline="") as fp:
    format_class = formats.detect(fp)
    if format_class is None:
        raise ValueError("Could not detect update data format")
    update_rows = list(format_class(fp).to_iterable())

allowed_labels = set(cl.labels())
observed_labels = {label for _text, label in update_rows}
if not observed_labels <= allowed_labels:
    raise ValueError(f"Unexpected labels: {observed_labels - allowed_labels}")

cl.update(update_rows)
```

### Difficult case: mixed CSV/JSON labels

A common bug is training on `"pos"`/`"neg"` but updating from JSON that uses
`"positive"`/`"negative"`. Normalize labels before update:

```python
def normalize_label(label):
    return {"positive": "pos", "negative": "neg"}.get(label, label)

more = [(text, normalize_label(label)) for text, label in more]
if not {label for _text, label in more} <= set(cl.labels()):
    raise ValueError("update labels do not match the trained classifier")
cl.update(more)
```

## 6. Inject a classifier into TextBlob

```python
from textblob import TextBlob

blob = TextBlob("The beer is good. The hangover is horrible.", classifier=cl)
print(blob.classify())
for sentence in blob.sentences:
    print(sentence, sentence.classify())
```

Sentence objects derived from the blob share the same classifier. Sentence
splitting is a separate NLP operation; if sentence classification fails with a
missing-corpus message, run TextBlob corpus setup or classify known sentence
strings directly.

## 7. Custom feature extractors

One-argument extractor:

```python
def first_last_features(document):
    tokens = document.split() if isinstance(document, str) else list(document)
    if not tokens:
        return {"empty": True}
    return {f"first={tokens[0].lower()}": True, f"last={tokens[-1].lower()}": True}

cl = NaiveBayesClassifier(train, feature_extractor=first_last_features)
```

Two-argument extractor using training vocabulary:

```python
def vocabulary_features(document, train_words):
    tokens = set(document.lower().split()) if isinstance(document, str) else set(document)
    return {f"has={word}": word in tokens for word in train_words}
```

TextBlob's wrapper first tries `feature_extractor(document, word_set)`. If that
raises `TypeError` or `AttributeError`, it retries as `feature_extractor(document)`.
This is why one-argument extractors work. Avoid accidental `TypeError` inside a
two-argument extractor because the fallback can hide the original bug.

## 8. Inspect explanations

Naive Bayes:

```python
features = cl.informative_features(10)
cl.show_informative_features(10)
```

Decision Tree:

```python
from textblob.classifiers import DecisionTreeClassifier

dt = DecisionTreeClassifier(train)
print(dt.pretty_format(width=80))
print(dt.pseudocode())
```

Use `informative_features()` for structured data and
`show_informative_features()` for interactive display.

## 9. Positive Naive Bayes

```python
from textblob.classifiers import PositiveNaiveBayesClassifier

sports = ["The team won the game", "The goalkeeper caught the ball"]
background = ["The president spoke", "I lost the keys", "The show is over"]

pnb = PositiveNaiveBayesClassifier(sports, background)
print(pnb.classify("The team controlled the ball"))
pnb.update(new_positive_data=["The striker scored"], new_unlabeled_data=["A cat slept"])
```

Do not pass CSV/JSON/TSV file objects into the Positive Naive Bayes constructor.
Normalize positive and unlabeled collections yourself.

## 10. MaxEnt workflow

`MaxEntClassifier` wraps NLTK's maximum entropy classifier. It supports
`classify()` and `prob_classify()`, but training can be slower than Naive Bayes.
Bound training explicitly when using it as a smoke or interactive workflow:

```python
from textblob.classifiers import MaxEntClassifier

me = MaxEntClassifier(train)
me.train(max_iter=10, trace=0)
print(me.classify("a short example"))
```

If optional numerical dependencies or runtime are a problem, use
`NaiveBayesClassifier` unless MaxEnt is required.
