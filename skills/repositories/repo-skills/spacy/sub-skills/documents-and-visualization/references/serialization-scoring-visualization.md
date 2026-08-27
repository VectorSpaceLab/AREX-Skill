# Serialization, scoring, and displaCy

This reference covers compact document storage, annotation scoring, and visualization output checks.

## `DocBin`

`DocBin` is the preferred way to store many docs compactly. It stores token hashes and selected annotations, not pickle objects.

| API | What it does |
| --- | --- |
| `DocBin(attrs=..., store_user_data=False, docs=None)` | Create a new bin with the chosen token attributes. |
| `add(doc)` | Add one doc to the bin. |
| `merge(other)` | Merge another bin with matching attributes. |
| `get_docs(vocab)` | Rebuild docs using the shared vocab. |
| `to_bytes` / `from_bytes` | Serialize or restore in memory. |
| `to_disk` / `from_disk` | Save or load a `.spacy` file. |

Key notes:

- `ORTH` and `SPACY` are always serialized, even if you do not list them in `attrs`.
- Use `store_user_data=True` if you want custom extension values and `Doc.user_data` preserved.
- Rebuild docs with the same shared `Vocab` that will consume them later.
- If a `DocBin` round-trip looks wrong, inspect the string table and the attrs list first.

Example:

```python
from spacy.tokens import DocBin

doc_bin = DocBin(attrs=["ENT_IOB", "ENT_TYPE"], store_user_data=True)
doc_bin.add(doc)
blob = doc_bin.to_bytes()
reloaded = DocBin().from_bytes(blob)
docs = list(reloaded.get_docs(nlp.vocab))
```

## Scoring basics

For this skill, scoring mostly means checking document annotations, not running a large training loop.

| Scorer API | Best for |
| --- | --- |
| `Scorer.score_tokenization(examples)` | Tokenization accuracy and span-level token boundaries. |
| `Scorer.score_token_attr(examples, attr)` | One token attribute such as `pos` or `tag`. |
| `Scorer.score_token_attr_per_feat(examples, attr)` | Morphological features and per-feature scores. |
| `Scorer.score_spans(examples, attr)` | Entity or span precision/recall/F-score. |
| `Scorer.score_deps(examples, attr)` | Dependency scores for docs with parse annotations. |
| `Scorer.score_cats(examples, attr)` | Document-level classification scores like `Doc.cats`. |

Useful rules:

- Build examples with `Example(predicted_doc, reference_doc)`.
- Use `doc.has_annotation(...)` or `doc.ents` / `doc.spans` to decide which scorer is appropriate.
- Tokenization scoring skips docs with unknown spaces.
- For span scoring, choose the getter and `has_annotation` policy that match the annotation you are evaluating.

Tiny example:

```python
from spacy.scorer import Scorer
from spacy.training import Example

scores = Scorer.score_spans([Example(pred_doc, ref_doc)], "ents")
assert scores["ents_f"] == 1.0
```

## displaCy render helpers

The public helpers you will use most often are:

| Helper | When to use it |
| --- | --- |
| `displacy.render(...)` | Return SVG/HTML markup for a doc or manual dict input. |
| `displacy.serve(...)` | Launch a small web server for interactive inspection. |
| `displacy.parse_deps(...)` | Convert docs to dependency-visualizer data. |
| `displacy.parse_ents(...)` | Convert docs to entity-visualizer data. |
| `displacy.parse_spans(...)` | Convert docs to span-visualizer data. |

`displacy.render` accepts these styles:

- `dep` for dependency arcs
- `ent` for named entities
- `span` for span visualizations

Signature shape:

```python
render(docs, style="dep", page=False, minify=False, jupyter=None, options={}, manual=False)
```

### Input rules

| Input | Allowed when | Notes |
| --- | --- | --- |
| `Doc` | `manual=False` | The helper parses the doc into render data. |
| `Span` | `manual=False` | The span is converted to a doc first. |
| `dict` or list of dicts | `manual=True` | You must provide the render data yourself. |

Manual data shapes:

- dependency view: `{"words": [...], "arcs": [...]} `
- entity view: `{"text": ..., "ents": [...]}`
- span view: `{"text": ..., "spans": [...], "tokens": [...]}`

### Options that matter here

| Style | Common options |
| --- | --- |
| `dep` | `collapse_punct`, `collapse_phrases`, `fine_grained`, `add_lemma`, colors and layout options |
| `ent` | `colors`, `ents`, `kb_url_template` |
| `span` | `colors`, `spans_key`, `kb_url_template` |

Important span-visualizer detail:

- The span renderer reads `doc.spans["sc"]` by default.
- If your spans live under a different key, pass `options={"spans_key": "your_key"}`.

### Output checks

When you render a sample, check for these things:

- HTML contains the expected text snippets and labels.
- Dependency output contains the token tags and arc labels you expect.
- Entity output escapes HTML-sensitive characters.
- Span output contains the span labels and respects overlapping spans.
- Manual dict input is sorted by offsets before rendering when needed.

Example:

```python
html = displacy.render(doc, style="span", options={"spans_key": "ruler"})
assert "ORG" in html
assert "Bank of China" in html
```

## Practical warnings

- `displacy.render("raw text")` is the wrong input type; pass a `Doc`, `Span`, or manual dicts.
- `style` must be one of `dep`, `ent`, or `span`.
- If you render dependency visualizations, the doc should already have dependency annotations or you should provide manual dependency data.
- If you render entity or span visualizations on a blank pipeline, set entities or spans yourself first.
