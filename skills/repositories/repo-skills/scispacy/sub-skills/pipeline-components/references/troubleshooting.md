# Troubleshooting

## Purpose

Use this when a pipeline component does not register, tokenize, segment, or serialize the way you expect.

## Common failures

### `ValueError: Can't find factory for 'abbreviation_detector'`

**Cause:** `scispacy.abbreviation` was never imported in the current process.

**Fix:** import the module before adding the pipe.

```python
import scispacy.abbreviation
nlp.add_pipe("abbreviation_detector")
```

The same rule applies to `hyponym_detector` and `pysbd_sentencizer`.

---

### `doc.to_bytes()` or multiprocessing fails after abbreviation detection

**Cause:** the detector was created with the default `make_serializable=False`.

**Fix:** switch to serializable abbreviation output.

```python
nlp.add_pipe("abbreviation_detector", config={"make_serializable": True})
```

---

### Sentence boundaries look wrong around abbreviations or newlines

**Cause:** the custom sentence-segmentation pipe is missing, or it is not the first pipe in the pipeline.

**Fix:** add `pysbd_sentencizer` near the front of the pipeline and keep abbreviation-aware tokenization rules in place.

---

### The tokenizer no longer matches the expected BIO or whitespace layout

**Cause:** the default spaCy tokenizer is still active.

**Fix:** replace it with `combined_rule_tokenizer` for biomedical text, or `WhitespaceTokenizer` for already tokenized input.

---

### `hyponym_detector` produces no patterns

**Cause:** the document lacks POS/dependency annotation or the sentence text does not match a Hearst pattern.

**Fix:** use a fully loaded spaCy model such as `en_core_sci_sm`, and test with a canonical pattern like `such as` before debugging the broader corpus.

---

### `en_core_sci_scibert` is slow on CPU

**Cause:** the transformer-backed model is heavier than the small biomedical models.

**Fix:** use `en_core_sci_sm` or `en_core_sci_md` for routine pipeline development. Keep `en_core_sci_scibert` for cases that really need the transformer model.

---

### Legacy evaluation helper names do not exist

**Cause:** old notes or scripts may mention `combined_rule_sentence_segmenter`, but the current exported component is `pysbd_sentencizer`.

**Fix:** use the current component names from the API reference and the bundled smoke script instead of following the stale helper name.
