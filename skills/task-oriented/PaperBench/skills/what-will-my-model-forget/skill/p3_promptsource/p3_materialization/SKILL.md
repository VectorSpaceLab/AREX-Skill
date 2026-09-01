---
name: p3_materialization
description: Materialize PromptSource/P3-style template collections into prompted dataset records with template identity, metadata propagation, coverage counts, and rendering diagnostics.
---

# P3 Prompted Dataset Materialization

Use this skill when converting a small PromptSource-style template collection and dataset examples into prompted training or evaluation records without reading the original PromptSource repository.

## Inputs

- `dataset_name`: dataset identifier.
- `subset_name`: optional subset/configuration identifier.
- `templates`: JSON list of template records with `id`, `name`, `template`, `answer_choices`, and metadata fields.
- `examples`: JSON list of dataset examples.

## Outputs

A JSON object with `records`, `summary`, `metadata_reports`, and `errors`.

## Workflow

1. Validate each template's metadata with the metadata-quality helper.
2. Render each template over each example using the template-rendering helper.
3. Emit only non-skipped, successful prompted records.
4. Preserve dataset identity, template id/name, input, target, and metadata in every record.
5. Summarize template count, example count, produced records, skipped rows, errors, and represented metrics.

## Validation

Run:

```bash
python tests/test_p3_materialization.py
python scripts/materialize_p3.py --dataset-name synthetic_snli --examples-json '[{"premise":"A dog runs","hypothesis":"An animal moves","label":0}]' --templates-json '[{"id":"t1","name":"nli","template":"{{premise}} Question: {{hypothesis}}? ||| {{answer_choices[label]}}","answer_choices":["Yes","No","Maybe"],"metrics":["Accuracy"],"valid_outputs_stated":true,"reference":"paper example"}]'
```

## Limitations

This skill materializes supplied examples. It does not download benchmark datasets, launch the PromptSource UI, or reproduce large-scale P3 training.
