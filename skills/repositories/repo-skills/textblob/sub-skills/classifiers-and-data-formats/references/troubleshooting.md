# TextBlob classifier troubleshooting

Most TextBlob classifier failures come from data shape, file-like handling,
missing tokenization corpora, label drift, or malformed feature extractors.

## Quick symptom table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `FormatError: Could not automatically detect format...` | File-like data is not recognizable or sampled JSON is incomplete | Pass explicit `format="csv"`, `"json"`, or `"tsv"`; fix content; or register a format. |
| `ValueError: '<name>' format not supported.` | Explicit `format=` is not registered | Use a built-in name or call `formats.register(name, FormatClass)` first. |
| `ValueError: train_set is probably malformed.` | Training data is not two-item `(document, label)` examples | Preview rows; validate lengths; convert dicts/dataframes to pairs. |
| Unpacking errors | Filename string, plain list of strings, or bad CSV/TSV row was treated as training data | Open files and pass file objects; validate every row. |
| `NameError: This blob has no classifier. Train one first!` | `TextBlob` was created without `classifier=cl` | Recreate with `TextBlob(text, classifier=cl)` or use `Blobber(classifier=cl)`. |
| Missing corpus / lookup error | Default feature extraction tokenizes strings with TextBlob/NLTK tokenizers | Run TextBlob corpus setup, or use token-list documents/custom extractor. |
| Sentence `.classify()` fails but direct `cl.classify()` works | `blob.sentences` needs sentence-tokenizer data | Run corpus setup or classify known sentence strings directly. |
| `prob_classify` missing | Classifier class lacks probability API | Use `NaiveBayesClassifier` or `MaxEntClassifier`. |
| MaxEnt slow/noisy | NLTK MaxEnt defaults can be expensive | Call `train(max_iter=..., trace=0)` or use Naive Bayes. |
| Accuracy drops after update | Label mismatch or changed preprocessing | Validate incoming labels against `set(cl.labels())`. |

## File-like versus path confusion

Correct:

```python
with open("train.csv", encoding="utf-8", newline="") as fp:
    cl = NaiveBayesClassifier(fp, format="csv")
```

Incorrect:

```python
cl = NaiveBayesClassifier("train.csv", format="csv")
```

Classifier constructors read files only when the object is file-like. A filename
string is just a string and usually becomes malformed training data.

## Debug malformed data

```python
def preview_examples(examples, n=5):
    for index, example in enumerate(list(examples)[:n], start=1):
        print(index, repr(example), type(example).__name__)
        if not isinstance(example, (list, tuple)) or len(example) != 2:
            raise ValueError(f"bad classifier example at row {index}")
```

For JSON, the top-level value must be an array and each object must contain
`text` and `label`. For CSV/TSV, check quoting and embedded delimiters.

## Missing corpus during classifier work

String training and default feature extraction use TextBlob tokenization. If the
target environment lacks required NLTK tokenizer data, training or
classification may fail with a TextBlob missing-corpus message.

Safe remedy:

```bash
python -m textblob.download_corpora
```

If the workflow must avoid corpora, train on token lists and provide a custom
extractor that does not call TextBlob tokenizers.

## Feature extractor checklist

1. Confirm the signature is one of:

   ```python
   def extractor(document): ...
   def extractor(document, train_words): ...
   ```

2. Call it directly on the document shape the classifier will see:

   ```python
   features = extractor("simple text")
   assert isinstance(features, dict)
   ```

3. Support both strings and token lists when needed:

   ```python
   def extractor(document):
       tokens = document.split() if isinstance(document, str) else list(document)
       return {f"has={tok.lower()}": True for tok in tokens}
   ```

4. Avoid raising `TypeError` or `AttributeError` inside a two-argument extractor;
   TextBlob catches those exceptions to support one-argument fallback.
5. Return deterministic feature names and simple values such as booleans,
   strings, or numbers.

## TextBlob sentence classification checklist

```python
blob = TextBlob("Good API. Bad docs.", classifier=cl)
for sentence in blob.sentences:
    print(sentence.classify())
```

Check:

- The blob was constructed with `classifier=cl`.
- The classifier's feature extractor accepts raw sentence strings.
- Sentence tokenizer corpora are available.
- The sentence text is close enough to the training domain.

## Format registry checklist

```python
from textblob import formats
print(formats.get_registry().keys())
```

Verify:

- Registration ran before classifier construction.
- The class implements `to_iterable(self)` and `detect(cls, stream)`.
- `detect()` returns `True` for a short sample of its format and `False` for
  unrelated formats.
- `to_iterable()` returns `[(text, label), ...]`, not dictionaries or strings.
- The custom name does not overwrite a built-in by accident.

## Label drift checklist

```python
old_labels = set(cl.labels())
new_labels = {label for _text, label in new_examples}
if not new_labels <= old_labels:
    raise ValueError(f"new labels not present in classifier: {new_labels - old_labels}")
```

If you intentionally add a new label class, include enough examples for that
class and re-run held-out accuracy checks.

## Safe smoke

Run the bundled script from the classifier sub-skill directory or by absolute
path:

```bash
python scripts/classifier_smoke.py --json
python scripts/classifier_smoke.py --skip-decision-tree
```

The script trains tiny in-memory classifiers and creates temporary CSV/JSON/TSV
data. It does not read original repository fixtures.
