# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| A loader returns empty or malformed data | The packaged dictionary archives are missing or the wrong loader name was used | Reinstall the package and confirm the loader name against the catalog.
| `extract_keyphrase` or `extract_summary` fails early | `jiojio` or the packaged idf/topic resources are unavailable | Reinstall with the repository's normal dependencies and rerun the smoke script.
| `analyse_freq_words` errors on input shape | The text was not tokenized first | Pass token lists, not raw strings.
| `new_word_discovery` returns `{}` | The corpus is too small for PMI / entropy thresholds | Use a larger UTF-8 line corpus or lower the thresholds for a smoke test.
| `llm_test_dataset_loader` rejects the version | Version was passed as a float | Use `'1.0'` or `'1.1'`.
| `MELLM` cannot evaluate | No callable LLM APIs or no external evaluation files were supplied | Treat the constructor as the local smoke check and wire real APIs only when you have credentials and data.
| `byte_level_bpe` is missing from the root package | The object lives under `jio.bpe.byte_level_bpe` | Import or call it through the `bpe` submodule.
