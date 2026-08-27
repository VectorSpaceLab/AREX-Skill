# Troubleshooting

## Cross-cutting issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `import jionlp` prints a banner | Expected import side effect | Ignore it; the package is still usable.
| `AttributeError: module 'numpy' has no attribute 'unicode'` | NumPy is too new for the CWS/POS converters | Install a NumPy 1.x release older than 1.24, such as `numpy==1.23.5`, and rerun the smoke check.
| `jio_help` waits for input | The console helper is interactive | Use `scripts/search_api_docs.py` for noninteractive keyword search.
| Dictionary loaders fail on first import | Packaged dictionary archives are missing or broken | Reinstall the package and confirm the packaged `jionlp/dictionary/` assets are present.
| `llm_test_dataset_loader()` rejects the version | The loader expects a string version | Pass `'1.0'` or `'1.1'`, not a float.

## When to escalate to a sub-skill
- Use `text-cleaning-and-extraction` for malformed HTML, boundary-sensitive removal, or file helper issues.
- Use `parsing-and-normalization` for ambiguous time, money, address, phone, ID, or plate parsing.
- Use `text-augmentation` for credentialed translation APIs, slow augmentation, or unexpected entity-offset shifts.
- Use `annotation-and-dataset-tools` for tag-length mismatches, BIOES/BI confusion, or NumPy compatibility issues.
- Use `dictionaries-and-language-analysis` for missing dictionary data, empty LLM test sets, or external JSON/API requirements.
