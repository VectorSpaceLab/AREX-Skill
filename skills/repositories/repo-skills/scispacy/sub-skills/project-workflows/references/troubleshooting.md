# Troubleshooting

## Purpose

Use this when a scispaCy data reader, evaluation helper, or project workflow does not parse inputs or produce metrics correctly.

## Common failures

### MedMentions parsing returns empty splits

**Cause:** the directory layout is incomplete or the PMID split files are missing.

**Fix:** confirm the MedMentions folder contains the five canonical files listed in the data-formats reference.

---

### BIO TSV reader drops sentences

**Cause:** the file is not truly two-column tab-separated BIO data, or blank lines are missing between sentences.

**Fix:** ensure each token line has exactly two tab-separated fields and that each sentence is terminated by an empty line.

---

### Overlapping entities disappear unexpectedly

**Cause:** `remove_overlapping_entities` greedily resolves chains by keeping the longest compatible spans.

**Fix:** verify the input spans are sorted and check whether the gold data contains overlapping annotations that need manual handling.

---

### `evaluate_ner` cannot load the model

**Cause:** the model path is wrong, the package is missing, or the model and spaCy minor versions do not match.

**Fix:** load the model separately with spaCy first, then rerun the evaluation helper once the model import works.

---

### `convert_freqs.py` raises `AssertionError: Cannot smooth your weird data`

**Cause:** the toy frequency file is too small or too degenerate for `PreshCounter.smooth()`.

**Fix:** use a more realistic fixture with more rows and more varied counts. The helper works on normal corpus-derived frequency files, but extremely tiny synthetic data may not be enough for the smoothing step.

---

### `export_umls_json.py` is slow or appears to hang

**Cause:** the UMLS META release is large and the export must scan several full text files.

**Fix:** this is expected for full UMLS exports. Use a smaller sample or a fixture-backed test if you only need to validate the workflow.

---

### `print_out_metrics.py` reports missing files

**Cause:** the expected package metric JSON files are not in the `packages/` directory structure the helper expects.

**Fix:** confirm the output folder names match the project naming convention before rerunning the reporter.

---

### Legacy sentence-splitting helper import is wrong

**Cause:** a legacy sentence-splitting evaluator imports `combined_rule_sentence_segmenter`, which is no longer exported by the package.

**Fix:** treat that file as reference-only and use `pysbd_sentencizer` with the current workflow helpers instead.

---

### GPU flag causes avoidable setup errors

**Cause:** `evaluate_ner.py` accepts `--gpu_id`, but a CPU-only host should not be forced into a GPU path.

**Fix:** leave the GPU flag unset unless you have already verified the accelerator backend and the model package supports it.
