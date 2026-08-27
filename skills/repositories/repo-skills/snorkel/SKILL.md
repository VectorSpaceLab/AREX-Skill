---
name: snorkel
description: "Operate Snorkel weak-supervision, data transform, classification,
  and slicing workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Snorkel

Use this repo skill when the task is about the installed Snorkel Python package:

- programmatic labels and weak supervision
- labeling functions, label matrices, LF analysis, and label models
- data-point mappers, preprocessors, spaCy preprocessing, and augmentation transforms
- PyTorch-backed Snorkel datasets, task graphs, classifiers, trainers, loggers, and metrics
- slicing functions, slice monitoring, and slice-aware classifiers
- optional Dask, local Spark, or spaCy paths owned by Snorkel APIs

Do not use this skill for generic PyTorch training, general Spark cluster administration, spaCy pipeline training unrelated to Snorkel preprocessors, cleanlab label-quality auditing, or source-repository maintenance unless the user explicitly names Snorkel APIs.

## Quick install check

Snorkel requires Python `>=3.11`.

```bash
pip install snorkel
python scripts/check_snorkel_install.py
```

Optional paths:

```bash
python scripts/check_snorkel_install.py --check-spacy-model
python scripts/check_snorkel_install.py --check-spark
```

Read [`references/installation-and-optional-dependencies.md`](references/installation-and-optional-dependencies.md) before adding Dask, spaCy, Spark, or TensorBoard-related dependencies.

## Route by task

| User intent or signal | Read next | Why |
| --- | --- | --- |
| `LabelingFunction`, `labeling_function`, `LFApplier`, `PandasLFApplier`, `LabelModel`, weak labels, label matrix `L`, LF coverage/overlap/conflict, majority voters | [`sub-skills/labeling/SKILL.md`](sub-skills/labeling/SKILL.md) | Owns programmatic labels and label-model workflows. |
| `Mapper`, `lambda_mapper`, `preprocessor`, `SpacyPreprocessor`, `TransformationFunction`, `TFApplier`, augmentation policy, synthetic label matrix | [`sub-skills/data-transforms/SKILL.md`](sub-skills/data-transforms/SKILL.md) | Owns data-point transforms that support labeling, slicing, and augmentation. |
| `DictDataset`, `DictDataLoader`, `Operation`, `Task`, `MultitaskClassifier`, `Trainer`, `Scorer`, metrics, checkpointing, TensorBoard, soft-label training | [`sub-skills/classification/SKILL.md`](sub-skills/classification/SKILL.md) | Owns discriminative model, trainer, logging, and evaluation APIs. |
| `SlicingFunction`, `SFApplier`, `slice_dataframe`, `add_slice_labels`, `convert_to_slice_tasks`, `SliceAwareClassifier`, `score_slices` | [`sub-skills/slicing/SKILL.md`](sub-skills/slicing/SKILL.md) | Owns slice creation, slice labels, and slice-aware modeling. |

## Common cross-workflow paths

### Weak supervision to classifier training

1. Use `labeling` to define LFs and produce an `L` matrix.
2. Use `labeling` to inspect `LFAnalysis` and fit `LabelModel` or a voter.
3. Use `labeling` to filter unlabeled rows.
4. Use `classification` to build `DictDataset` / `DictDataLoader` with hard or probabilistic labels.
5. Use `classification` to train/evaluate a `MultitaskClassifier` or `Trainer`.

### Text labeling or slicing with spaCy

1. Use `data-transforms` for `SpacyPreprocessor` details and model setup.
2. Use `labeling` for `NLPLabelingFunction` or `spark_nlp_labeling_function`.
3. Use `slicing` for `NLPSlicingFunction` or `nlp_slicing_function`.
4. Use root troubleshooting if the model or language package cannot load.

### Slice-aware classification

1. Use `slicing` to create SFs and an `S` recarray.
2. Use `classification` to understand the base `Task`, module pool, and tensor dataset.
3. Use `slicing` to create slice labels and `SliceAwareClassifier` dataloaders.
4. Use `classification` or `slicing` scoring depending on whether the user wants overall metrics or slice-specific metrics.

## References and scripts

- Source snapshot and refresh baseline: [`references/repo-provenance.md`](references/repo-provenance.md)
- Router metadata for managed imports: [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json)
- Installation and optional dependencies: [`references/installation-and-optional-dependencies.md`](references/installation-and-optional-dependencies.md)
- Cross-cutting troubleshooting: [`references/troubleshooting.md`](references/troubleshooting.md)
- Root install checker: [`scripts/check_snorkel_install.py`](scripts/check_snorkel_install.py)

## Validation approach

Start with the smallest safe check:

1. Run the root install checker.
2. Run the nearest sub-skill smoke script.
3. If optional Dask, spaCy, or Spark paths are involved, verify those optional dependencies before blaming Snorkel code.
4. For full native behavior checks, use the review artifacts produced during skill creation rather than adding source-checkout assumptions to runtime instructions.

## Operational caveats

- Snorkel uses `-1` as the abstain label across weak-label and metric helpers.
- `LabelModel` requires at least three labeling functions and a label matrix consistent with the configured cardinality.
- `DictDataset` labels must be `torch.Tensor` values.
- `SliceAwareClassifier` and `SliceCombinerModule` are binary-only in this version.
- Spark coverage in this skill is local Spark wrapper behavior, not production cluster deployment.
