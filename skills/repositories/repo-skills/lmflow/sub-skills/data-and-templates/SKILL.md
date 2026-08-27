---
name: data-and-templates
description: "Helps with LMFlow dataset schemas, conversation templates,
  validation, and dataset conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data and Templates

Use this sub-skill when the task is about LMFlow JSON datasets, dataset validation, conversation templates, or fixing schema errors before training, inference, or evaluation.

## Typical Triggers

- `conversation_template`
- `text_only`, `text2text`, `conversation`, `paired_conversation`, `text_to_textlist`, `text_to_scored_textlist`
- `Dataset.create_from_dict`, `Dataset.save`, `Dataset.sample`, `Dataset.train_test_split`
- `format my data`, `validate this dataset`, `template mismatch`, `custom chat template`

## What This Sub-Skill Owns

- LMFlow dataset layouts and required fields.
- Conversation template names and customization guidance.
- Safe dataset validation and listing helpers.
- Errors caused by missing fields, mixed types, bad template names, and multimodal dependency gaps.

## Read These First

- `references/data-formats.md` for the dataset shapes and required keys.
- `references/conversation-templates.md` for built-in templates and customization rules.
- `references/api-reference.md` for `Dataset` and `DatasetArguments` behavior.
- `references/troubleshooting.md` for predictable schema and template failures.
- `scripts/validate_lmflow_dataset.py` to check a file or directory.
- `scripts/list_lmflow_templates.py` to print the available template names.

## Workflow

1. Identify the dataset type and whether the user has one JSON file or a directory of files.
2. Check the required keys for that type.
3. Confirm the template name is a known LMFlow preset or an intentional custom template.
4. If the task is about repair, explain the exact missing keys or incompatible file layout.
5. Use the validator script before any training or inference command.

## Cross-Links

- Training and fine-tuning workflows that consume these datasets live in `../training-and-optimization/SKILL.md`.
- Inference and evaluation workflows that read the same formats live in `../inference-and-evaluation/SKILL.md`.
- Alignment workflows that require preference datasets live in `../post-training-alignment/SKILL.md`.

## Common Decisions

- Use `text_only` for raw text samples.
- Use `text2text` for paired input/output examples.
- Use `conversation` for ShareGPT-style conversations with `messages`.
- Use `paired_conversation`, `paired_text_to_text`, or `text_to_scored_textlist` for preference data.
- Use `empty` or `empty_no_special_tokens` when the dataset already contains conversation markers.

## What Not To Do

- Do not keep mixed dataset types in one directory of JSON files.
- Do not guess required keys; validate them.
- Do not ask future agents to open the original repository docs when the bundled references already contain the schema.
- Do not treat multimodal support as available unless the optional dependency is installed.
