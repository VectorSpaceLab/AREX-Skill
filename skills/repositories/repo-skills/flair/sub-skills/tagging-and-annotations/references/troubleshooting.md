# Troubleshooting Tagging and Annotations

This page covers common Flair annotation, tokenization, prediction, serialization, and visualization failures. CPU with a public pip-installed `flair` package is the verified baseline; downloads and optional tokenizer/model backends are unverified unless the active environment proves them.

## Tokenization drift or lost token labels

Symptoms:

- Predicted spans do not align with expected character offsets.
- `RegexpTagger` raises that a match span is overlapping with a token.
- Token labels disappear after changing `sentence.tokenizer`.
- Serialized/deserialized spans come back missing or attached to different token ranges.

Causes and fixes:

1. **Tokenizer changed after annotation.** Flair lazily retokenizes on the next `sentence.tokens` access when `sentence.tokenizer` changes. Span/relation labels are re-applied by offsets where possible, but token-level labels are not reliably preserved. Decide tokenization before annotating or re-run the model after retokenization.
2. **Regex boundaries do not match token boundaries.** `RegexpTagger` can only label whole-token spans. Print `[(t.text, t.start_position, t.end_position) for t in sentence]`, compare to `match.span(...)`, then adjust the regex, use `SegtokTokenizer(additional_split_characters=[...])`, or choose `SpaceTokenizer` / `NoTokenizer` intentionally.
3. **Sentence splitter offsets misunderstood.** `token.start_position` is relative to `sentence.text`; add `sentence.start_position` for document-level offsets.
4. **Pretokenized input reconstructed spaces differently.** `Sentence(["a", "b"])` reconstructs text with single spaces and uses no further tokenizer. Use raw text plus a tokenizer when exact original whitespace must be preserved.

Quick diagnostic:

```python
for sentence in sentences:
    print("sentence", sentence.start_position, repr(sentence.to_original_text()))
    print([(t.text, t.start_position, t.end_position, t.whitespace_after) for t in sentence])
    print([(label.typename, label.value, label.data_point.text) for label in sentence.get_labels()])
```

## Model downloads, cache, and offline runs

Symptoms:

- `Classifier.load("ner")` or `TextClassifier.load("sentiment")` hangs or fails with network errors.
- Models download into an unexpected user cache.
- A workflow that was intended to be no-download loads Hugging Face resources.

Fixes:

- Treat pretrained model names as download-capable. Use manual labels or `RegexpTagger` for no-download tests.
- Set cache-related environment before importing `flair` when downloads are permitted. A typical policy is to set `FLAIR_CACHE_ROOT` to a deliberate cache directory and keep it out of generated public skill files if it is machine-specific.
- Use `Classifier.load(local_model_path)` only with a path supplied by the user or a project artifact that is valid in the current environment; do not bake private paths into reusable skill instructions.
- Keep `FLAIR_DEVICE=cpu` for the verified baseline unless GPU use is explicitly tested.
- If loading a concrete class fails, try `Classifier.load(model_id)` for public model IDs because it dispatches to the correct classifier implementation.

## Label-layer confusion

Symptoms:

- `sentence.get_labels()` returns more labels than expected.
- `sentence.get_spans("ner")` is empty but `sentence.get_labels("ner")` has labels.
- A second prediction overwrote manual labels.
- NER, POS, sentiment, and relation outputs are mixed together.

Fixes:

- Always pass the target layer when extracting production outputs: `get_labels("ner")`, `get_spans("ner")`, `get_relations("relation")`.
- Remember that `get_labels("layer")` returns labels from sentence, token, span, and relation data points; `get_spans("layer")` returns only `Span` objects that have that layer.
- For sequence taggers, span-predicting models add `Span` labels by default. If token labels are required, call `predict(..., force_token_predictions=True)` and read token labels.
- Prediction methods remove existing labels in the target layer before adding new predictions. Use `label_name="new_layer"` when preserving a gold/manual layer.
- `RegexpTagger` uses each mapping label as both layer name and label value. If you need `layer="quote", value="DIRECT"`, add labels manually after finding spans or post-process the regex output.

Layer discipline example:

```python
sentence[0:2].add_label("gold_ner", "PER")
tagger.predict(sentence, label_name="pred_ner")
print(sentence.get_spans("gold_ner"))
print(sentence.get_spans("pred_ner"))
```

## Offsets and serialization failures

Symptoms:

- `Sentence.from_dict(...)` fails importing a tokenizer class.
- Optional tokenizer model is missing during deserialization.
- Relation labels round-trip but downstream code cannot find expected spans.
- JSON serialization fails because custom objects were added to metadata or because the legacy `labels` field contains live `Label` objects.

Fixes:

- Prefer `SegtokTokenizer`, `SpaceTokenizer`, `NoTokenizer`, or `StaccatoTokenizer` for portable serialized examples.
- For `SpacyTokenizer`, `SciSpacyTokenizer`, and `JapaneseTokenizer`, verify optional packages and model resources before deserializing; otherwise use a CPU baseline tokenizer and document that exact tokenization changed.
- Keep label metadata JSON-friendly if it will leave the process.
- Use `Sentence.from_dict(sentence.to_dict())` for Flair's own round-trip.
- If writing strict JSON from Flair 0.15.1, keep the structured `payload["annotations"]` data and omit or convert `payload["labels"]` if it contains `Label` objects.
- Check `sentence.to_original_text()`, token text/offsets, `get_spans(layer)`, and `get_labels(layer)` immediately after deserialization.

## Optional tokenizer dependencies

Symptoms and fixes:

- `SpacyTokenizer("en_core_web_sm")` fails: install `spacy` and the model, or use `SegtokTokenizer` if exact spaCy alignment is not required.
- `SciSpacyTokenizer()` or `SciSpacySentenceSplitter()` fails: install compatible `spacy`, `scispacy`, and `en_core_sci_sm`; route biomedical entity workflows through the biomedical sub-skill.
- `JapaneseTokenizer(...)` fails or exits: install `konoha` plus the selected backend (`mecab`, `janome`, or `sudachi`) and any system packages. If Japanese tokenization is required, treat this as a blocker rather than falling back silently.
- `TokenizerWrapper.from_dict(...)` raises `NotImplementedError`: this is expected because arbitrary Python functions cannot be reconstructed automatically. Recreate the wrapper function manually in the running process.

## HTML visualization issues

Symptoms:

- HTML omits labels.
- Entities appear in the wrong places.
- Overlapping entities render poorly.

Fixes:

- Pass the correct layer with `render_ner_html(sentences, label_name="your_layer")`; default is `"ner"`.
- Use it for non-overlapping span-style labels. Token-level or relation labels are not visualized meaningfully by the NER HTML renderer.
- Validate offsets first with `sentence.get_spans(layer)` and `span.start_position` / `span.end_position`.
- Render one layer at a time when the sentence contains gold/predicted or nested labels.
- The renderer returns an HTML string. Writing files is optional and should be done only to an explicitly selected output path.

## Empty sentence or unexpected no labels

Symptoms:

- Empty sentence warning.
- `predict` returns no predictions.
- `get_label("layer")` returns an `O` label.

Fixes:

- Strip or filter empty strings before creating sentences for model inference.
- Confirm `len(sentence) > 0`; lazy tokenization may reveal that the selected tokenizer produced no tokens.
- For `get_label`, remember that missing labels return a default `O` label with score `0.0`. Use `get_labels(layer)` and check length when absence must be detected.

## Safe local verification

Use the bundled smoke script for annotation mechanics without downloads:

```bash
python scripts/annotation_smoke.py --json
```

It checks manual sentence/token/span/relation labels, `DataPair`, `RegexpTagger`, SegTok/space/no tokenization, sentence splitting, `Sentence.to_dict()` / `from_dict()`, and NER HTML rendering using only in-memory data.
