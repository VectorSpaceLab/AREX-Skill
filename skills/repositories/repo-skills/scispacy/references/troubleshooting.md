# Troubleshooting

## Purpose

Use this for cross-cutting scispaCy failures that do not belong to one narrow sub-skill. It covers install/import problems, model registration, linker cache failures, and version mismatches.

## Common failures

### 1) `ValueError: Can't find factory for 'abbreviation_detector'`

**Likely cause:** the factory module was never imported, so spaCy never registered the component.

**Fix:** import the module before calling `nlp.add_pipe`.

```python
import scispacy.abbreviation
import scispacy.hyponym_detector
```

Then retry `nlp.add_pipe("abbreviation_detector")` or `nlp.add_pipe("hyponym_detector")`.

---

### 2) `doc.to_bytes()` fails after adding abbreviations

**Likely cause:** the abbreviation detector was created without `make_serializable=True`.

**Fix:** create the pipe with serializable output when you need multiprocessing or byte serialization.

```python
nlp.add_pipe("abbreviation_detector", config={"make_serializable": True})
```

The serialized abbreviation objects use the keys `short_text`, `short_start`, `short_end`, `long_text`, `long_start`, and `long_end`.

---

### 3) Model compatibility warnings

**Likely cause:** the model package and spaCy minor version do not match.

**Fix:** install a model package that matches the spaCy minor version you are using. In the verified setup, `en_core_web_sm` 3.7.1 matched spaCy 3.7.5 and `en_core_sci_sm` 0.5.4 also loaded successfully with spaCy 3.7.5.

If the warning is only informational and the smoke check passes, you can usually continue.

---

### 4) Linker smoke or custom KB build emits an nmslib CPU warning

**Symptom:** a message such as `Your CPU supports instructions that this binary was not compiled to use: SSE3 SSE4.1 SSE4.2 AVX AVX2` appears.

**Likely cause:** the installed nmslib wheel is generic and not CPU-optimized for the current host.

**Fix:** this is usually a performance warning, not a functional failure. If the linker smoke passes, you can continue. If performance matters, rebuild or reinstall nmslib from source on a compatible host.

---

### 5) `scispacy_linker` with `resolve_abbreviations=True` does not use long forms

**Likely cause:** the abbreviation detector is missing from the pipeline, or the document has no `Doc._.abbreviations` extension yet.

**Fix:** add the abbreviation detector before the linker.

```python
import scispacy.abbreviation
nlp.add_pipe("abbreviation_detector")
nlp.add_pipe("scispacy_linker", config={"resolve_abbreviations": True, "linker_name": "umls"})
```

---

### 6) Custom KB linker build returns no candidates

**Likely cause:** the KB is too small or too sparse for the default char-3gram `min_df=10` vectorizer in `create_tfidf_ann_index`.

**Fix:** add more aliases or use a larger KB. For smoke tests, build a tiny KB with repeated character patterns across at least 10 aliases.

---

### 7) Remote KB or model downloads fail

**Likely cause:** network access, proxy, or cache issues while `cached_path` fetches UMLS/MeSH/GO/HPO/RxNorm artifacts.

**Fix:**
- retry with network access enabled,
- pre-download the artifact and pass a local path,
- or inspect the scispaCy cache directory if the artifact should already exist.

Do not treat a cached-path failure as a package import failure unless the import itself also fails.

---

### 8) Legacy sentence-splitting helper looks wrong

A legacy sentence-splitting evaluator imports `combined_rule_sentence_segmenter`, but the current package exports `pysbd_sentencizer`.

**Fix:** treat the legacy evaluation script as reference-only. Use the current component names and the bundled smoke helper instead of relying on that file.

---

### 9) Package import fails after `pip install scispacy`

**Likely cause:** a dependency mismatch or an incomplete environment.

**Fix:**
- run `python -m pip check`,
- confirm the environment uses Python 3.11 or another supported 3.9–3.12 interpreter,
- reinstall the model packages that the workflow actually needs,
- and rerun the bundled smoke script.

If the failure mentions missing `spacy`, `nmslib`, `scipy`, `scikit-learn`, or `pysbd`, install the runtime dependencies again rather than debugging the repository code first.
