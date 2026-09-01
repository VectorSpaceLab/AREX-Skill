---
name: prompt_metadata_quality
description: Validate PromptSource-style prompt metadata and community quality constraints for natural-language prompts, metrics, answer choices, and target format.
---

# Prompt Metadata Quality

Use this skill when reviewing PromptSource/P3-style prompt records before adding them to a prompt collection or using them in a recovery experiment.

## Inputs

- `metadata`: JSON object with fields such as `name`, `metrics`, `answer_choices`, `original_task`, `valid_outputs_stated`, `language`, and `reference`.
- `rendered_examples`: optional JSON list of rendered prompt records with `input` and `target`.

## Outputs

A JSON validation report with `ok`, `errors`, `warnings`, and `checked_fields`.

## Workflow

1. Require a prompt name and reference or rationale.
2. Validate metrics against the PromptSource metric vocabulary.
3. Validate language tags when supplied.
4. Check consistency between valid-output metadata and answer choices.
5. Inspect rendered examples for natural-language task statements and concise targets.
6. Return actionable review messages without mutating the prompt.

## Validation

Run:

```bash
python tests/test_prompt_metadata_quality.py
python scripts/validate_metadata.py --metadata-json '{"name":"based on passage","metrics":["Accuracy"],"answer_choices":["Yes","No","Maybe"],"valid_outputs_stated":true,"reference":"paper example"}'
```

## Limitations

This skill provides deterministic review checks. It does not replace human judgment for prompt usefulness or downstream model performance.
