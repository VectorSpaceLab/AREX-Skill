# Troubleshooting

Use this page for package-wide issues that are not specific to one model family or one serving mode.

## First checks

1. Confirm the package installs and imports in the intended environment.
2. Run `python -m pip check`.
3. Run `python -m deeppavlov --help`.
4. Run `python scripts/smoke_deeppavlov_pipeline.py`.
5. If the error is family-specific, reroute to `text-models`, `retrieval-qa`, `serving`, or `pipelines`.

## Install and import issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: deeppavlov` | The package was not installed into the active environment. | Install `deeppavlov` with pip or use the prepared editable environment. |
| `pip check` reports broken requirements | A required dependency was downgraded, removed, or conflicted with another install. | Reinstall the package in a clean prefix or repair the conflicting dependency set. |
| The CLI works in one shell but not another | Different Python interpreters or environments are active. | Re-run the command with the intended environment's Python. |

## Optional dependency patterns

DeepPavlov has many family-specific extras. Missing dependency errors usually mean the wrong family was chosen rather than a broken package.

| Missing dependency | Common families |
| --- | --- |
| `spacy`, `en_core_web_sm`, `ru_core_news_sm` | entity extraction, retrieval/QA, some tokenization paths |
| `torch`, `transformers` | BERT-based classifiers, taggers, relation extraction, multitask, SQuAD, ODQA, embedders |
| `datasets` | GLUE / SuperGLUE / multitask / some regression readers |
| `fasttext` | FAQ and some classification paths |
| `hdt`, `rapidfuzz`, `whapi` | KBQA and relation-ranking paths |
| `kenlm`, `lxml`, `sortedcontainers`, `sacremoses` | spelling correction |

If you only need a quick smoke, choose a CPU-friendly path that does not require the missing family-specific dependency.

## Configuration and path issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Alias warning appears | The config stem maps through a compatibility alias. | Switch to the canonical config name. |
| Config resolves but loads the wrong files | `metadata.variables` or `DP_*` overrides point to unexpected roots. | Inspect `DP_SETTINGS_PATH`, `DP_ROOT_PATH`, and `DP_CONFIGS_PATH`. |
| A download seems skipped | Existing resource files or `.done` markers are being reused. | Rebuild the relevant data/index files in a new path or clear the stale artifacts. |
| A model-specific config still fails after the generic smoke passes | The family needs data or dependencies that the smoke does not cover. | Reroute to the model-family sub-skill and check its data/dependency reference. |

## Backend and hardware notes

- CPU import and a tiny pipeline smoke are enough for the general package skill.
- Do not assume GPU verification from a CPU-only smoke.
- If the user asks about CUDA, PyTorch, Transformers, or other accelerator-specific workflows, use the relevant family sub-skill and verify that backend separately.

## Safe recovery path

For a clean, offline package check:

```bash
python -m pip check
python -m deeppavlov --help
python scripts/smoke_deeppavlov_pipeline.py
```

If those pass, the failure is usually in a specific config, data layout, or optional dependency rather than in the base package install.
