# Troubleshooting

## Purpose

Use this when candidate generation, KB loading, or linker behavior is not what you expected.

## Common failures

### `resolve_abbreviations=True` appears to do nothing

**Cause:** the abbreviation detector is not in the pipeline yet.

**Fix:** import and add the abbreviation detector before the linker.

```python
import scispacy.abbreviation
nlp.add_pipe("abbreviation_detector")
nlp.add_pipe("scispacy_linker", config={"resolve_abbreviations": True, "linker_name": "umls"})
```

---

### Tiny custom KB builds return no useful candidates

**Cause:** the ANN vectorizer uses char-3grams with `min_df=10`. A very small KB may not create enough surviving features.

**Fix:** add more aliases, repeat shared character patterns across the KB, or test the linker against a larger KB.

---

### `nmslib` emits a CPU instruction warning

**Symptom:** a warning says the binary was not compiled to use SSE3/SSE4.1/SSE4.2/AVX/AVX2.

**Meaning:** the wheel is generic and not host-optimized.

**Fix:** usually none is needed if the smoke passes. Rebuild from source only if you need host-specific performance.

---

### KB or index downloads fail

**Cause:** network, proxy, or cache issues while `cached_path` fetches remote KB/index artifacts.

**Fix:**

- provide a local KB file or directory,
- pre-populate the scispaCy cache,
- or retry with a working network connection.

Do not treat a cache fetch failure as a code bug until the local path and network situation are clear.

---

### `KnowledgeBase(None)` or similar constructor errors

**Cause:** the loader was called without a real KB source.

**Fix:** pass a JSON/JSONL file path or an iterable of `Entity` objects, or use one of the built-in KB subclasses that already knows its default path.

---

### The linker build is very slow

**Cause:** `create_tfidf_ann_index` is constructing the full ANN index and can be expensive for large KBs.

**Fix:**

- build once and reuse the saved index directory,
- lower your expectations for smoke testing,
- or use a tiny KB for verification and a separate large KB for real use.

---

### Backward-compatibility alias confusion

**Cause:** some older notes refer to `UmlsEntityLinker` or `scispacy.umls_linking`.

**Fix:** prefer `EntityLinker` from `scispacy.linking`. The old alias exists only for compatibility.
