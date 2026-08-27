# Troubleshooting

Use this reference when config validation, data conversion, or training setup fails.

## Fast triage

1. Run `debug config` first if the failure might be config or registry related.
2. Run `debug data` next if config is valid but the corpora or labels may be wrong.
3. Run `validate` if installed model packages no longer match the current spaCy version.
4. Use `find-function` when a registry name is missing or a custom code file was not imported.

## Symptom matrix

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Config validation error`, `field required`, `extra fields not permitted` | The config is incomplete or structurally invalid. | Run `init fill-config`, then `debug config --show-functions --show-variables`. If the config refers to custom registry entries, load them with `--code` or `--code-path`. |
| `Config file not found`, missing `[paths]` values, or `debug data` cannot load the corpus | A path override is missing or the training files are not where the config expects them. | Set `--paths.train` and `--paths.dev`, or fix the `[paths]` block. Verify that the `.spacy` files exist before training. |
| `invalid entity annotations`, `misaligned tokens`, `invalid whitespace entity spans`, or crossing-boundary entity warnings | The annotation offsets do not match the tokenizer, or the data crosses sentence boundaries unexpectedly. | Fix the source annotations, verify tokenization, and rebuild the `.spacy` file. Use `Doc.char_span(..., alignment_mode="strict")` to detect bad offsets and adjust the source data if it returns `None`. |
| `Low number of examples for label` or `No examples for texts WITHOUT new label` | The training split is too small or too imbalanced. | Add more examples, include negative examples, or keep the smoke run separate from the real training corpus. |
| `Pipeline can be initialized with data` fails in `debug data` | Initialization code, registry lookups, or component setup is broken. | Check `--code`, inspect registry names with `find-function`, and simplify the config until initialization succeeds. |
| `Corpus is loadable` fails in `debug data` | The corpus path or file format is wrong. | Re-run conversion, verify the `.spacy` file, and confirm the path overrides are correct. |
| `validate` reports incompatible packages | The installed pipeline package does not match the current spaCy version. | Run `validate`, then reinstall a compatible model package or switch to a matching spaCy version. |
| GPU flags do nothing or fail on this host | Optional GPU support is absent or unverified. | Drop `--gpu-id` for the smoke run, or install and verify the matching CUDA or Apple extra separately. Do not treat CPU fallback as GPU verification. |
| `Couldn't find registered function` or `Unknown function registry` | The custom code file was not imported, or the registry name is wrong. | Pass the correct `--code` / `--code-path`, make sure the decorator runs at import time, and use `find-function` to locate the registered name. |
| `find-threshold` returns identical scores or says the threshold is not applicable | The selected component does not use a threshold, or the score key is wrong. | Use a thresholded component such as multilabel text classification or span categorization, and choose a numeric score like `cats_macro_f` or `spans_sc_f`. |
| Training is slow or expensive | You are trying to run the full optimization loop too early. | Keep this sub-skill to validation smoke: validate config, validate data, or run a tiny CPU-only training step with a very small `--training.max_steps`. |

## Recovery patterns

- Config issue: fix the config first, then rerun `debug config`.
- Data issue: fix the annotations or paths, then rerun `debug data`.
- Package issue: fix installed versions, then rerun `validate`.
- Registry issue: fix imports or `--code`, then rerun `debug config` or `train`.

When in doubt, prefer the smallest possible smoke that proves the wiring without starting a full training run.
