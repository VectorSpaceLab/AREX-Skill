# Doc, Token, Span, and DocBin API

## Verified object-model facts

Installed package inspection verified these core signatures in spaCy 3.8.15:

- `spacy.blank(name: str, *, vocab=True, config={}, meta={}) -> Language`
- `spacy.load(name, *, vocab=True, disable=[], enable=[], exclude=[], config={}) -> Language`
- `Language.__init__(vocab=True, *, max_length=1000000, meta={}, create_tokenizer=None, create_vectors=None, batch_size=1000, **kwargs)`
- `Language.pipe(texts, *, as_tuples=False, batch_size=None, disable=[], component_cfg=None, n_process=1)`
- `Doc.char_span(start_idx, end_idx, label=0, kb_id=0, vector=None, alignment_mode='strict', span_id=0)`
- `Doc.to_bytes(*, exclude=())`, `Doc.from_bytes(bytes_data, *, exclude=())`, `Doc.to_disk(path, *, exclude=())`, `Doc.from_disk(path, *, exclude=())`, `Doc.to_json(underscore=None)`, `Doc.from_json(doc_json, *, validate=False)`, `Doc.to_array(py_attr_ids)`, `Doc.from_array(attrs, array)`
- `Span.as_doc(*, copy_user_data=False, array_head=None, array=None)`, `Span.char_span(...)`, `Span.similarity(other)`
- `Token.nbor(i=1)`, `Token.set_morph(features)`, `Token.similarity(other)`
- `DocBin()` plus `DocBin(attrs=..., store_user_data=...)` in the test suite

## Core behavior to remember

- `spacy.blank('en')` creates a blank English pipeline without pretrained weights.
- `nlp(text)` tokenizes and then applies any configured components in order.
- `nlp.pipe(texts)` yields `Doc` objects; it is usually preferred for batches.
- `Doc.char_span` can return `None` if offsets do not align with token boundaries. Use `alignment_mode='contract'`, `'expand'`, or validate the offsets first.
- Extension attributes are registered on `Doc`, `Span`, and `Token` with `set_extension`.
- `DocBin` is the preferred binary container for training data and round-tripping annotated `Doc` objects.

## Minimal examples

### Blank pipeline

```python
import spacy
nlp = spacy.blank("en")
doc = nlp("Hello, spaCy!")
assert [t.text for t in doc] == ["Hello", ",", "spaCy", "!"]
```

### Safe `DocBin` round-trip

```python
from spacy.tokens import Doc, DocBin
import spacy

nlp = spacy.blank("en")
doc = nlp("Some text")
doc.cats = {"A": 1.0}
blob = DocBin(docs=[doc], store_user_data=True).to_bytes()
reloaded = list(DocBin().from_bytes(blob).get_docs(nlp.vocab))[0]
assert reloaded.text == "Some text"
```

### Character-span recovery

```python
span = doc.char_span(0, 4, alignment_mode="expand")
if span is None:
    raise ValueError("Offsets do not align with token boundaries")
```

## When to inspect this file

Read this file whenever a user asks about token offsets, span alignment, serialization, extension attributes, or the exact object returned by a text-processing API.
