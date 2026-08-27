# TextBlob classifier data formats

TextBlob classifiers can read in-memory examples or opened file-like objects.
The built-in file formats are registered as `csv`, `json`, and `tsv`.

## In-memory shape

Use a sequence of two-item examples:

```python
train = [("I love this car", "pos"), ("I do not like this car", "neg")]
```

The first item may be a string or an iterable of tokens. The second item is the
label. Use consistent label spelling and type across training, update, and test
data.

## CSV

Schema: one training/test example per row, with `text,label`.

```csv
I love this sandwich,pos
This is an amazing place,pos
I do not like this restaurant,neg
```

Use Python CSV quoting when text contains commas:

```csv
"Nice, simple API",pos
"Bad, confusing output",neg
```

Read it as an opened file:

```python
from textblob.classifiers import NaiveBayesClassifier

with open("train.csv", encoding="utf-8", newline="") as fp:
    cl = NaiveBayesClassifier(fp, format="csv")
```

## TSV

Schema: one `text<TAB>label` row per example. TSV is useful when texts often
contain commas.

```python
with open("train.tsv", encoding="utf-8", newline="") as fp:
    cl = NaiveBayesClassifier(fp, format="tsv")
```

## JSON

Schema: a JSON array of objects. Each object must contain `text` and `label`.

```json
[
  {"text": "I love this sandwich", "label": "pos"},
  {"text": "I do not like this restaurant", "label": "neg"}
]
```

Read it with:

```python
with open("train.json", encoding="utf-8") as fp:
    cl = NaiveBayesClassifier(fp, format="json")
```

Newline-delimited JSON is not the built-in JSON shape; convert it to an array
or register a custom format.

## Automatic detection

`textblob.formats.detect(fp, max_read=1024)` tries each registered format
against a file-like object and returns the matching format class or `None`.

```python
from textblob import formats

with open("train.csv", encoding="utf-8", newline="") as fp:
    format_class = formats.detect(fp)
    if format_class is None:
        raise ValueError("unsupported classifier data format")
    rows = list(format_class(fp).to_iterable())
```

Important details:

- `detect` expects a file-like object with `read()` and `seek()`; non-file-like
  values return `None`.
- `detect` samples only the first `max_read` bytes/characters by default. Large
  JSON arrays may need explicit `format="json"` because a partial JSON sample
  is not valid JSON.
- Built-in detection checks the registry in order. Because CSV sniffing is
  attempted before JSON in the default registry, short or comma-heavy examples
  can be ambiguous. Use explicit `format=` in production.
- Detection resets the stream to the beginning after each attempt, so the
  returned format class can read the file immediately.

Classifier constructors and `accuracy()` can also auto-detect file-like data
when `format=None`:

```python
with open("train.tsv", encoding="utf-8", newline="") as fp:
    cl = NaiveBayesClassifier(fp)
```

## Registry and custom formats

```python
from textblob import formats
print(formats.get_registry().keys())  # csv, json, tsv, plus custom entries
```

Register a pipe-delimited format:

```python
from textblob import formats
from textblob.classifiers import NaiveBayesClassifier

class PipeDelimitedFormat(formats.DelimitedFormat):
    delimiter = "|"

formats.register("psv", PipeDelimitedFormat)

with open("train.psv", encoding="utf-8", newline="") as fp:
    cl = NaiveBayesClassifier(fp, format="psv")
```

Register a non-delimited source by subclassing `formats.BaseFormat`:

```python
from textblob import formats

class MyFormat(formats.BaseFormat):
    def __init__(self, fp, **kwargs):
        self.fp = fp
        self.kwargs = kwargs

    @classmethod
    def detect(cls, stream):
        return stream.startswith("MYFORMAT\n")

    def to_iterable(self):
        return [("example text", "pos")]

formats.register("myformat", MyFormat)
```

`register()` mutates the process-wide registry. Use unique names in libraries or
tests to avoid collisions with existing format names.

## Error behavior

| Situation | Typical exception or signal | Recovery |
| --- | --- | --- |
| Auto-detection cannot find a format for file-like training data | `textblob.exceptions.FormatError` from classifier construction | Pass explicit `format=...`, fix file content, or register a custom format. |
| Explicit format name is not registered | `ValueError` such as `'<name>' format not supported.` | Check `formats.get_registry()` or call `formats.register()`. |
| Filename string passed instead of opened file object | Treated as in-memory data and usually fails as malformed training data | Use `open(...)` and pass the file object. |
| JSON array lacks `text` or `label` | `KeyError` while converting JSON to examples | Normalize JSON objects to the required keys. |
| CSV/TSV row does not have exactly two fields | Training, feature extraction, or accuracy may fail while unpacking examples | Validate every row as `(text, label)` before classifier construction. |
| Labels differ across train/update/test (`pos` vs `positive`) | Extra unintended class labels or poor accuracy | Normalize labels before training and before `update()`. |

## Safe validation helper

```python
def validate_examples(examples):
    normalized = []
    for index, item in enumerate(examples, start=1):
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError(f"example {index} is not a two-item pair")
        text, label = item
        if not isinstance(label, (str, bool)):
            raise ValueError(f"example {index} has unsupported label type {type(label).__name__}")
        normalized.append((text, label))
    return normalized
```
