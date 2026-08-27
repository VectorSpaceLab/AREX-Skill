# Troubleshooting

Use this matrix when a document, matcher, ruler, scorer, or visualizer behaves unexpectedly.

| Symptom | Likely cause | Recovery | Quick check |
| --- | --- | --- | --- |
| `Doc.char_span(...)` returns `None` | The character offsets do not align with token boundaries under `strict` alignment. | Inspect the token offsets, then retry with `alignment_mode="contract"` or `alignment_mode="expand"`, or adjust the offsets to exact boundaries. | `doc.char_span(start, end, alignment_mode="expand")` |
| Matcher or ruler returns no results | Tokenization mismatch or the pattern expects annotations that are not present. | Compare `nlp.make_doc(text)` to the pattern token sequence, use `tokenizer.explain`, and make sure the needed `POS`, `DEP`, or `LEMMA` annotations exist. | `print([t.text for t in nlp.make_doc(text)])` |
| `PhraseMatcher` looks correct but still misses hits | The phrase docs were built with the wrong pipeline state or the wrong match attribute. | Build phrase docs with the same tokenizer and annotations you will have at runtime, or switch `attr` to the token attribute you actually need. | `PhraseMatcher(..., validate=True)` |
| `DocBin` round-trip gives odd labels or string lookups | The consuming code is not using the shared `Vocab` or the bin was built with different attrs than the reader expects. | Rebuild the docs with the same vocab that will consume them and keep the attrs list consistent on both sides. | `list(doc_bin.get_docs(nlp.vocab))` |
| `Doc.set_extension` / `Token.set_extension` / `Span.set_extension` raises `ValueError` | The extension name is already registered, or the getter/method/setter combination is invalid. | Remove the old extension before re-registering, or replace it intentionally with `force=True`. | `obj.has_extension(name)` |
| `doc.sents`, `doc.noun_chunks`, `DependencyMatcher`, or dependency displaCy fails | The doc does not have dependency annotations. | Use a pipeline with a parser, or build a manual doc with `heads` and `deps` when you only need a smoke test. | `doc.has_annotation("DEP")` |
| displaCy raises on input type or style | The input is raw text, the style is unsupported, or `manual=True` is missing for dict input. | Pass a `Doc`, `Span`, or the correct dict structure; keep `style` to `dep`, `ent`, or `span`; use `options={"spans_key": ...}` for span output. | `displacy.render(doc, style="ent")` |
| displaCy dep output looks empty | There is no dependency annotation on the doc. | Use a parsed doc or manual dependency data. | `doc.has_annotation("DEP")` |
| displaCy ent or span output is empty | The doc has no entities/spans yet. | Set `doc.ents` or `doc.spans[...]` manually first, or use `EntityRuler` / `SpanRuler`. | `len(doc.ents)` / `len(doc.spans.get("ruler", []))` |
| `spacy.load("en_core_web_sm")` fails | No pretrained package is installed. | Use `spacy.blank("en")` for blank-pipeline work, or install the model package separately when a pretrained pipeline is required. | `nlp = spacy.blank("en")` |

## Recovery patterns

### Offset recovery for `char_span`

```python
span = doc.char_span(start, end)
if span is None:
    span = doc.char_span(start, end, alignment_mode="expand")
```

### Tokenization recovery for matchers

1. Print the runtime tokenization.
2. Rebuild the pattern using the same tokenizer output.
3. Validate the pattern and re-run the match.

### Extension recovery

```python
if Doc.has_extension("source_id"):
    Doc.remove_extension("source_id")
Doc.set_extension("source_id", default=None, force=True)
```

### No-model recovery

- Start from `spacy.blank("en")`.
- Set entities or spans manually.
- Build manual dependency docs with `heads` and `deps` if you need dependency visualization or dependency matching.
- Use `DocBin` and the smoke scripts to verify behavior without downloading a model.
