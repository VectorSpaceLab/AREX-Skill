# Annotation Workflows

This reference distills Flair's annotation APIs for a public, pip-installed `flair` package. It is CPU-first and uses no private checkout paths.

## Core data types and label layers

| Type | Create/use | Important behavior |
| --- | --- | --- |
| `Sentence` | `Sentence("George Washington went to Washington.")` | Holds original text, lazy tokens, sentence-level labels, and the central annotation registry for token/span/relation labels. |
| `Token` | Iterate `for token in sentence`, index `sentence[3]`, or construct `Token("word")` for pre-tokenized input. | Token indices in display are zero-based; `token.idx` is one-based. `token.start_position` / `end_position` are offsets within `sentence.text`. |
| `Span` | Slice a sentence: `sentence[0:2]`. | Contiguous token range. Labels added to a span are also registered on the sentence layer. |
| `Relation` | `Relation(sentence[0:2], sentence[4:5])` | Directed relation between two spans in the same sentence. Labels added to it are retrieved through the sentence layer. |
| `Label` | Produced by `add_label`, predictions, or direct `Label(data_point, value, score)`. | `label.value`, `label.score`, `label.data_point`, `label.metadata`, and `label.typename` are the usual fields. |
| `DataPair` | `DataPair(sentence_a, sentence_b)` | Holds two data points for pair-style tasks; text is represented as `first || second`. |

Layer names are independent from class values. In `span.add_label("ner", "PER", score=0.99)`, `"ner"` is the annotation layer and `"PER"` is the class value. Keep layer names stable (`"ner"`, `"pos"`, `"sentiment"`, `"relation"`, etc.) so extraction and visualization can target one layer at a time.

## Manual labels

```python
from flair.data import DataPair, Relation, Sentence

sentence = Sentence("George Washington went to Washington.")

# Sentence-level label.
sentence.add_label("topic", "history")

# Token-level label: token indexing uses Python's zero-based indexes.
sentence[2].add_label("pos", "VERB")

# Span-level labels. Multiple layers can refer to the same Span.
person = sentence[0:2]
place = sentence[4:5]
person.add_label("ner", "PER", score=1.0)
person.add_label("role", "president")
place.add_label("ner", "LOC")

# Relation labels are also layer-scoped.
Relation(person, place).add_label("relation", "visited")

pair = DataPair(Sentence("first text"), Sentence("second text"))
```

Use `set_label(layer, value)` when exactly one label should remain on that layer for a data point. Use `add_label` when multiple labels are allowed.

## Extract predictions and annotations

```python
# All labels from all layers, sorted by their attached data point.
all_labels = sentence.get_labels()

# Only one layer. This returns Label objects regardless of whether they attach to
# the sentence, tokens, spans, or relations.
ner_labels = sentence.get_labels("ner")
for label in ner_labels:
    print(label.value, label.score, label.data_point.text, label.typename)

# Span or relation objects when you need structured endpoints.
for span in sentence.get_spans("ner"):
    print(span.text, span.start_position, span.end_position, span.get_label("ner").value)

for relation in sentence.get_relations("relation"):
    print(relation.first.text, relation.second.text, relation.get_label("relation").value)
```

Important distinctions:

- `sentence.get_labels("ner")` returns `Label` objects whose `.data_point` may be a `Span` or a `Token` depending on the model or manual labels.
- `sentence.get_spans("ner")` returns only span data points that have that layer.
- `sentence.get_labels()` with no layer mixes sentence, token, span, and relation labels; it is useful for debugging but risky in downstream code.
- `token.get_label("pos")` returns a default `Label(token, "O")` when there is no such label, which is convenient for tag sequences but can hide missing predictions if used without checks.

## Pretrained prediction APIs

Pretrained models are public package resources, but loading a model by name can download from the configured Flair/Hugging Face cache. Treat downloads as optional unless already allowed.

```python
from flair.data import Sentence
from flair.nn import Classifier

sentence = Sentence("George Washington went to Washington.")

tagger = Classifier.load("ner")      # May download if not cached.
tagger.predict(sentence)             # Adds predictions into the model's default layer.

for label in sentence.get_labels("ner"):
    print(label.data_point.text, label.value, label.score)
```

Useful variants:

```python
# Batch inference over many Sentence objects.
sentences = [Sentence("A sentence."), Sentence("Another sentence.")]
tagger.predict(sentences, mini_batch_size=16)

# Keep existing labels by predicting into a new layer.
tagger.predict(sentence, label_name="ner_model_v1")

# For SequenceTagger specifically, request per-token labels rather than span labels
# when a span-predicting model would otherwise create Span objects.
from flair.models import SequenceTagger
sequence_tagger = SequenceTagger.load("ner")
sequence_tagger.predict(sentence, label_name="ner_token_view", force_token_predictions=True)

# TextClassifier labels the sentence-level data point.
from flair.models import TextClassifier
classifier = TextClassifier.load("sentiment")
classifier.predict(sentence, label_name="sentiment")
```

Prediction methods mutate the passed sentences and usually return `None`. Read results from the same `Sentence` objects after prediction.

Common pretrained model IDs used in Flair tutorials include:

- Sequence/span or token tagging: `"ner"`, `"ner-fast"`, `"ner-large"`, `"pos"`, `"pos-fast"`, `"upos"`, `"chunk"`, `"frame"`, `"relations"`.
- Text classification: `"sentiment"`, `"sentiment-fast"`.
- Biomedical models such as HunFlair/HunFlair2 route through the biomedical sub-skill because they often need SciSpaCy, linking dictionaries, and extra layer discipline.

## Rule-based tagging with `RegexpTagger`

`RegexpTagger` is a safe no-download option for local span annotations. Each mapping entry is `(regex, label)` or `(regex, label, group_index)`. The label string is used both as the layer name and the label value.

```python
from flair.data import Sentence
from flair.models import RegexpTagger

sentence = Sentence('Der sagte: "das ist durchaus interessant"')

tagger = RegexpTagger([
    (r'["„»]((?:(?=(\\?))\2.)*?)[”"“«]', "quote_part", 1),
    (r'["„»]((?:(?=(\\?))\2.)*?)[”"“«]', "quote"),
])
tagger.predict(sentence)

print(sentence.get_label("quote_part").data_point.text)  # das ist durchaus interessant
print(sentence.get_label("quote").data_point.text)       # "das ist durchaus interessant"
```

The regex match span must align with token boundaries. If a match starts or ends inside a token, Flair raises an exception instead of creating a partial-token span.

## Serialization round trip

`Sentence.to_dict()` captures text, tokens, sentence/span/relation annotations, language code, start position, tokenizer configuration, and a legacy `labels` field. `Sentence.from_dict(...)` reconstructs the `Sentence` and reapplies annotations. In Flair 0.15.1, the legacy `labels` field may contain live `Label` objects, so strict JSON export should drop or convert that field after confirming the structured `annotations` data is present.

```python
from flair.data import Relation, Sentence
from flair.tokenization import SegtokTokenizer

original = Sentence("George Washington went to Washington.", use_tokenizer=SegtokTokenizer())
original.add_label("category", "HISTORICAL_EVENT")
person = original[0:2]
place = original[4:5]
person.add_label("ner", "PERSON")
place.add_label("ner", "LOCATION")
Relation(person, place).add_label("relation", "WENT_TO")

payload = original.to_dict()
json_safe_payload = {**payload, "labels": []}  # optional when exporting through strict JSON
recreated = Sentence.from_dict(payload)

assert recreated.to_original_text() == original.to_original_text()
assert [(s.text, s.get_label("ner").value) for s in recreated.get_spans("ner")] == [
    ("George Washington", "PERSON"),
    ("Washington", "LOCATION"),
]
assert [label.value for label in recreated.get_labels("relation")] == ["WENT_TO"]
```

Serialization caveats:

- Reconstructing a tokenizer requires its class and optional dependencies to be installed. `TokenizerWrapper` explicitly marks itself non-reconstructable.
- The tokenizer configuration is public package state, but custom functions, private model objects, and local file paths should not be placed in skill examples.
- For strict JSON, export the structured `annotations` data and omit or convert the legacy `labels` list if it contains live `Label` objects.
- Offsets in stored annotations are robust only when text and tokenization still allow the original spans to be mapped.

## HTML visualization

Use Flair's NER HTML renderer for quick span visualization. It expects a single non-overlapping span layer.

```python
from flair.data import Sentence
from flair.visual.ner_html import render_ner_html

sentence = Sentence("Boris Johnson will become the next UK prime minister.")
sentence[0:2].add_label("ner", "PER")
sentence[7:8].add_label("ner", "LOC")

html = render_ner_html(
    sentence,
    label_name="ner",
    colors={"PER": "#F7FF53", "LOC": "yellow", "O": "#ddd"},
)
```

`render_ner_html` returns an HTML string; writing it to a file is optional. If overlapping spans or multiple annotation layers need visualization, render one layer at a time or build a custom visualizer.

## End-to-end no-download skeleton

```python
from flair.data import Relation, Sentence
from flair.models import RegexpTagger
from flair.splitter import SegtokSentenceSplitter
from flair.visual.ner_html import render_ner_html

text = 'George Washington went to Washington. He said "hello".'
sentences = SegtokSentenceSplitter().split(text)

first = sentences[0]
first[0:2].add_label("ner", "PER")
first[4:5].add_label("ner", "LOC")
Relation(first[0:2], first[4:5]).add_label("relation", "visited")

RegexpTagger((r'"hello"', "quote")).predict(sentences[1])

round_trip = Sentence.from_dict(first.to_dict())
html = render_ner_html(round_trip, label_name="ner")
```
