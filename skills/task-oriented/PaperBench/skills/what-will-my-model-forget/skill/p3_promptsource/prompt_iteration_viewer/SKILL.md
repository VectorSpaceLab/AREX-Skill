---
name: prompt_iteration_viewer
description: Apply PromptSource-style templates across multiple examples and summarize browse, sourcing, and review diagnostics for prompt iteration.
---

# Prompt Iteration Viewer

Use this skill when you need a UI-neutral version of PromptSource's browse/sourcing workflow: render prompt variations over examples, preserve diagnostics, and summarize coverage.

## Inputs

- `examples`: JSON list of dataset example dictionaries.
- `templates`: JSON list with `id`, `name`, `template`, optional `answer_choices`, and metadata.
- `choice_index`: deterministic choice helper index.
- `include_skipped`: whether skipped rows should appear in output rows.

## Outputs

A JSON report with `rows`, `coverage`, `variation_summary`, and `errors`.

## Workflow

1. For every template/example pair, call the prompt template rendering helper.
2. Keep raw rendering diagnostics separate from rendered input and target.
3. Count produced, skipped, and error rows per template.
4. Summarize prompt variation names and target variants.
5. Use the report for prompt review or recovery evidence without changing targets.

## Validation

Run:

```bash
python tests/test_prompt_iteration_viewer.py
python scripts/iterate_prompts.py --examples-json '[{"premise":"A dog runs","hypothesis":"An animal moves","label":0}]' --templates-json '[{"id":"t1","name":"nli","template":"{{premise}} Question: {{hypothesis}}? ||| {{answer_choices[label]}}","answer_choices":["Yes","No","Maybe"]}]'
```

## Limitations

This skill does not launch Streamlit or load remote datasets. It provides the mechanism behind browse/iteration diagnostics on supplied examples.
