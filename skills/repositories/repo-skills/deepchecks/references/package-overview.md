# Deepchecks Package Overview

## When to read

Read this before choosing a sub-skill, selecting optional extras, or deciding whether Deepchecks has a CLI/API surface for a task.

## Package purpose

Deepchecks is a Python package for validating ML data and models. The open-source testing package centers on:

- Built-in **checks**: focused validations such as drift, label issues, weak segments, duplicates, outliers, performance reports, and data-format problems.
- Built-in **suites**: curated collections of checks for data integrity, train-test validation, and model evaluation.
- Modality-specific data containers: `Dataset` for tabular data, `TextData` for NLP data, and `VisionData` for images/detection/segmentation.
- Result objects: `CheckResult`, `CheckFailure`, and `SuiteResult` for display, HTML export, JSON serialization, and CI gates.

Deepchecks Monitoring and managed SaaS material is separate from this skill's primary package-testing scope.

## Install variants

Use the smallest install for the selected workflow:

| Workflow | Install guidance | Notes |
|---|---|---|
| Base + tabular | `pip install deepchecks` | Covers core results, tabular `Dataset`, tabular checks/suites, Plotly/HTML reports, sklearn/pandas/numpy dependencies. |
| NLP | `pip install "deepchecks[nlp]"` | Adds NLP checks and common tokenizer/embedding dependencies such as transformers, sentence-transformers, tiktoken, seqeval, textblob, and UMAP-related packages. |
| Optional NLP properties | `pip install "deepchecks[nlp-properties]"` | Adds fasttext-backed property support. Use only when the workflow needs those heavier property calculators. |
| Vision | `pip install "deepchecks[vision]"` plus compatible `torch`/`torchvision` when absent | `deepchecks.vision` imports PyTorch. Use a CPU build for CPU validation; install a CUDA build only for GPU-backed model execution. |

The inspected package metadata declared Python support through Python 3.10 for this source snapshot. If a modern environment fails to resolve old dependency pins, try a supported Python version before changing Deepchecks code.

## No public CLI entry point found

The package metadata and source inspection did not expose a console-script CLI. Treat Deepchecks as a Python API package. For automation, write small project-side Python scripts that import Deepchecks, run suites/checks, and save/gate results.

## Main API surfaces

| Surface | Use |
|---|---|
| `deepchecks.tabular.Dataset` | Wrap pandas/numpy tabular data and ML metadata. |
| `deepchecks.tabular.suites` | Run tabular data integrity, train-test validation, model evaluation, and full suites. |
| `deepchecks.nlp.TextData` | Wrap raw/tokenized text, labels, metadata, properties, and embeddings. |
| `deepchecks.nlp.suites` | Run NLP data integrity, train-test validation, model evaluation, and full suites. |
| `deepchecks.vision.VisionData` and `BatchOutputFormat` | Wrap image batches and task-specific labels/predictions. |
| `deepchecks.vision.suites` | Run vision data integrity, train-test validation, model evaluation, and full suites. |
| `deepchecks.core.CheckResult` and `SuiteResult` | Save, display, serialize, filter, and gate results. |

## Built-in datasets and examples

Deepchecks includes convenience dataset loaders in its package tree, but many loaders download data or model assets. For CI and diagnostics, prefer tiny local fixtures or the bundled smoke scripts in this skill. When using a public dataset loader, verify whether it downloads files, writes cache state, or trains a model before using it in an automated agent run.

## Latest-version check

Deepchecks can check for the latest package version on first import. In offline or privacy-sensitive automation, set:

```bash
export DISABLE_LATEST_VERSION_CHECK=True
```

The bundled install diagnostic sets this environment variable by default unless the caller has already provided a value.

## Sub-skill map

- Tabular data/model validation: [tabular-validation](../sub-skills/tabular-validation/SKILL.md).
- NLP text validation: [nlp-validation](../sub-skills/nlp-validation/SKILL.md).
- Vision/image validation: [vision-validation](../sub-skills/vision-validation/SKILL.md).
- Result export, CI, and integration adapters: [results-and-integrations](../sub-skills/results-and-integrations/SKILL.md).
