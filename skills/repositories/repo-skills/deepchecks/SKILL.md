---
name: deepchecks
description: "Route Deepchecks package tasks for ML data/model validation across
  tabular, NLP, vision, result export, and integration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Deepchecks Repo Skill

Use this repo skill when a task involves the Python package **Deepchecks** for validating ML data, train/test splits, model behavior, drift, weak segments, result reports, or CI gates across tabular, NLP, and computer-vision workflows.

## Install and import route

Start with the smallest install that matches the workflow:

```bash
pip install deepchecks
pip install "deepchecks[nlp]"              # NLP TextData, text checks, transformers-backed helpers
pip install "deepchecks[nlp-properties]"   # optional heavier text-property calculators
pip install "deepchecks[vision]"           # vision helpers; also install compatible torch/torchvision when needed
```

Then run the safe bundled diagnostic when imports or optional extras are uncertain:

```bash
python scripts/check_deepchecks_install.py --include-nlp --include-vision
```

Read [package overview](references/package-overview.md) for component boundaries, optional extras, Python-version notes, no-CLI expectations, and latest-version-check behavior. Read [root troubleshooting](references/troubleshooting.md) for install/import/display/optional dependency failures. Read [repository provenance](references/repo-provenance.md) before deciding whether this skill is stale for a checkout.

## Route by user task

| User asks for... | Load this sub-skill |
|---|---|
| pandas/numpy data validation, `Dataset`, tabular data integrity, train-test split validation, model evaluation, tabular checks/suites, custom scorers, supplied predictions or probabilities | [tabular-validation](sub-skills/tabular-validation/SKILL.md) |
| raw or tokenized text, `TextData`, text classification/token classification labels, text metadata/properties/embeddings, NLP suites/checks, tokenizer/model-download avoidance | [nlp-validation](sub-skills/nlp-validation/SKILL.md) |
| images, object detection, semantic segmentation, `VisionData`, `BatchOutputFormat`, PyTorch/TensorFlow/custom loaders, vision checks/suites, torch/torchvision or CUDA questions | [vision-validation](sub-skills/vision-validation/SKILL.md) |
| `CheckResult`/`SuiteResult` display, HTML reports, JSON serialization/recovery, pytest assertions, CI gates, GitHub Actions/Airflow/H2O/Hugging Face adapter patterns | [results-and-integrations](sub-skills/results-and-integrations/SKILL.md) |

## Operating rules for future agents

1. Choose the data modality first; each modality uses a different Deepchecks data container and validation context.
2. Prefer built-in suites for first-pass coverage, then switch to individual checks when the user names a specific issue or threshold.
3. Use explicit metadata (`label`, categorical columns, task type, label map, properties, embeddings, prediction/probability arrays) instead of relying on inference when the user has schema knowledge.
4. Avoid downloads in diagnostic or CI paths. Prefer tiny local fixtures, precomputed predictions, precomputed embeddings/properties, and bundled smoke scripts.
5. Save reports before failing CI. Route result persistence and gates to `results-and-integrations` instead of duplicating export logic in modality sub-skills.
6. Treat visible GPUs as optional unless the user specifically needs GPU-backed model execution. Deepchecks validation workflows can often be prepared and diagnosed with CPU-capable dependencies.
7. Do not tell users to run original repository examples or tests as part of package use. Use the bundled scripts and distilled references in this skill tree.

## Bundled diagnostics

- [scripts/check_deepchecks_install.py](scripts/check_deepchecks_install.py): check base/NLP/vision imports and optional torch CUDA status without running suites or downloading data.
- Each modality sub-skill has its own smoke helper for tiny local `Dataset`, `TextData`, or `VisionData` construction.

## When not to use this skill

- The task is about Deepchecks Monitoring self-hosted deployment or managed SaaS operations rather than the open-source testing package APIs.
- The task is generic ML training, model serving, dataset labeling, or experiment tracking without Deepchecks checks, suites, or result artifacts.
- The task is maintainer-only release, benchmark, docs-build, or repository CI infrastructure work unless the user explicitly asks to modify this Deepchecks checkout.
