---
name: prompt_template_rendering
description: Render PromptSource-style Jinja prompt templates into natural-language input/target pairs with answer choices, deterministic choices, skip handling, and structured diagnostics.
---

# Prompt Template Rendering

Use this skill when you need to apply a PromptSource-style prompt template to dataset example dictionaries without depending on the original PromptSource repository.

## Inputs

- `example`: JSON object containing dataset fields.
- `template`: string with exactly one `|||` separator between input and target halves.
- `answer_choices`: optional JSON list exposed to the template.
- `choice_index`: optional deterministic index for the `choice()` helper.

## Outputs

A JSON object with `ok`, `input`, `target`, `skipped`, and `errors` fields.

## Workflow

1. Validate that the template contains exactly one `|||` separator.
2. Render the two halves with Jinja2 using strict undefined variables.
3. Add `answer_choices` and a deterministic `choice()` helper to the rendering context.
4. Strip rendered input and target text.
5. Mark the result as skipped if either rendered half is empty.
6. Return structured diagnostics instead of raising uncaught rendering errors.

## Validation

Run:

```bash
python tests/test_prompt_template_rendering.py
python scripts/render_prompt.py --example-json '{"premise":"A dog runs.","hypothesis":"An animal moves.","label":0}' --answer-choices-json '["Yes","No","Maybe"]' --template '{{premise}} Is it true that {{hypothesis}}? ||| {{answer_choices[label]}}'
```

## Limitations

This skill renders templates and validates prompt boundaries. It does not load Hugging Face datasets, run the PromptSource UI, or evaluate model predictions.
