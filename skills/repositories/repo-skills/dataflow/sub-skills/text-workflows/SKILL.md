---
name: text-workflows
description: "Text workflow guidance for CPU-safe filtering, prompt-driven
  generation, reasoning, code, conversations, Text2SQL, and text2model."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# text-workflows

Use this sub-skill when the task is about text data workflows: cleaning, filtering, prompting, generation, translation, reasoning, code synthesis, conversations, Text2SQL, or text2model preparation.

Start here:
- `references/data-formats.md` for expected columns, cache shapes, and run-key conventions
- `references/text-pipelines.md` for choosing CPU-safe vs model-backed stages
- `references/operator-catalog.md` for operator families and common inputs
- `references/text2model-workflow.md` when the task touches `dataflow text2model`
- `references/troubleshooting.md` for missing-column, API, model, database, and sandbox issues

Working rules:
- Keep pure CPU filters separate from API- or model-backed stages.
- Validate columns before generation or training.
- Prefer small, explicit key mappings such as `input_key`, `output_key`, or family-specific `input_*_key` / `output_*_key` names.
- Treat downloads, local model serving, SQL execution, sandbox code execution, and training as side-effecting steps.

If you need a synthetic starting point, run `scripts/make_text_fixture.py` first.

Route other concerns to the right sub-skill:
- pipeline/storage debugging -> `pipeline-foundations`
- serving or backend setup -> `serving-cli`
- document, PDF, RAG, or VQA workflows -> `document-vision-rag`
- Ray acceleration or actor wrapping -> `rayorch-acceleration`
