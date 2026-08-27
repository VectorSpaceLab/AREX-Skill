---
name: snips-nlu
description: "Use Snips NLU for intent parsing, slot filling, dataset/resource
  preparation, engine API workflows, CLI training/parsing, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Snips NLU

Use this repo skill when a task involves Snips NLU (`snips-nlu` / `snips_nlu`) for classical natural-language understanding: intent classification, slot filling, YAML/JSON dataset authoring, language resources, Python engine APIs, CLI training/parsing, metrics, or persisted NLU engine artifacts.

This skill targets Snips NLU `0.20.2` and model format `0.20.0`.

## Quick setup and health checks

Install the public package in a compatible Python environment:

```bash
pip install snips-nlu
python -m snips_nlu --help
python -m snips_nlu version
python -m snips_nlu model-version
```

For this old release, prefer Python 3.8 when modern Python versions cannot resolve pinned compiled dependencies. Read `references/installation-and-resources.md` for install/resource details and `references/troubleshooting.md` for cross-cutting failures.

Run the bundled read-only environment check when diagnosing setup:

```bash
python scripts/check_snips_nlu_environment.py --json
```

If the workflow needs language resources, download or link them explicitly; helpers in this skill do not perform network downloads silently:

```bash
python -m snips_nlu download en
python scripts/check_snips_nlu_environment.py --resource en --json
```

## Route by task

| Task | Read |
|---|---|
| Create or validate a Snips NLU YAML/JSON dataset, inspect entity schemas, convert YAML to JSON, or reason about supported languages/resources. | `sub-skills/dataset-and-resources/SKILL.md` |
| Use Python APIs such as `SnipsNLUEngine`, `fit`, `parse`, `get_intents`, `get_slots`, `persist`, `from_path`, configs, random seeds, or result schemas. | `sub-skills/engine-api/SKILL.md` |
| Build or troubleshoot `snips-nlu` / `python -m snips_nlu` commands for `generate-dataset`, `train`, `parse`, `download`, `link`, versions, or metrics. | `sub-skills/cli-workflows/SKILL.md` |
| Decide whether this generated skill is current for a checkout/version. | `references/repo-provenance.md` |

## Common workflow map

1. **Author data**: use `dataset-and-resources` to write YAML intent/entity files or JSON datasets.
2. **Validate/convert**: use bundled dataset scripts before training.
3. **Prepare resources**: use CLI download/link commands only when network/resource setup is approved.
4. **Train and parse**: use either the Python engine API (`engine-api`) or CLI command recipes (`cli-workflows`).
5. **Persist and reload**: use `engine-api` for artifact layout, model-version compatibility, and safe persistence checks.
6. **Evaluate**: use `cli-workflows` for metrics commands and optional `snips-nlu-metrics` dependency notes.

## Important API and CLI anchors

Verified public API signatures include:

- `SnipsNLUEngine(config=None, **shared)`
- `SnipsNLUEngine.fit(dataset, force_retrain=True)`
- `SnipsNLUEngine.parse(text, intents=None, top_n=None)`
- `SnipsNLUEngine.get_intents(text)` and `get_slots(text, intent)`
- `SnipsNLUEngine.persist(path)` and `SnipsNLUEngine.from_path(path, **shared)`
- `Dataset.from_yaml_files(language, filenames)`
- `validate_and_format_dataset(dataset)`
- `load_resources(name, required_resources=None)`

Verified CLI commands include `generate-dataset`, `train`, `parse`, `download`, `download-all-languages`, `download-entity`, `download-language-entities`, `link`, `cross-val-metrics`, `train-test-metrics`, `version`, and `model-version`.

## Boundaries and safety

- Do not treat this as a modern LLM or neural sequence-model training skill; Snips NLU is a classical NLU package for intent/slot extraction.
- Do not assume package install success on Python 3.11+ for Snips NLU `0.20.x`; use compatibility troubleshooting first.
- Do not run network resource downloads, long metrics sweeps, or training against user data unless the user requested those side effects.
- Do not rely on original repository docs, tests, or sample files at runtime; this skill bundles the needed references and helper scripts.
