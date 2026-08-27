---
name: promptify
description: "Routes Promptify's structured NLP task and evaluation workflows,
  including NER, classification, QA, custom Pydantic schemas, and dataset-based
  metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Promptify

Promptify is a structured-output NLP library built on LiteLLM, Pydantic, and Jinja templates. Use this skill when a user wants to create, call, or debug Promptify task objects, build prompts, parse structured JSON output, or evaluate task outputs against labeled data.

## Install and import

If you need the full library surface, install the checkout in editable mode with the evaluation extra:

```bash
python -m pip install -e '.[eval]'
```

If you only need the task APIs and not ROUGE or the evaluation helpers, use:

```bash
python -m pip install -e .
```

Minimal no-network import checks:

```bash
python -c "from promptify import NER, Classify, QA, Summarize, Task, get_cost_summary; print('core-ok')"
python -c "from promptify.eval import evaluate; print('eval-ok')"
```

For a safe local smoke test that does not call any provider, run:

```bash
python scripts/check_promptify.py --mode all
```

Read `references/repo-provenance.md` before deciding whether this skill matches the current checkout or should be refreshed.

## What this skill covers

- Structured task creation and execution: NER, classification, QA, summarization, extraction, generation, normalization, topic extraction, and custom Pydantic tasks.
- Prompt construction, parser behavior, model configuration, async and batch execution, and cost tracking.
- Dataset loading, metric selection, and evaluation of task outputs.
- Common runtime failures such as provider auth errors, invalid JSON output, schema mismatches, template path problems, and legacy tutorial API confusion.

## Route map

### 1. Structured task APIs
Read `sub-skills/structured-tasks/SKILL.md` when the request is about creating a task object, choosing built-in task classes, customizing prompts, using examples or labels, running batch or async calls, or debugging parser or provider failures.

This route also covers the shared runtime objects that support task execution, including `ModelConfig`, `LLMEngine`, `Parser`, `PromptBuilder`, `get_cost_summary`, and `setup_logging`.

### 2. Evaluation workflows
Read `sub-skills/evaluation/SKILL.md` when the request is about `load_dataset`, `evaluate`, metric selection, CSV or JSON dataset formats, ROUGE, or interpreting evaluation failures.

### 3. Cross-cutting references
- `references/overview.md` for the current public import map and a quick orientation.
- `references/troubleshooting.md` for install, import, provider, parse, template, and legacy API mismatch issues.
- `references/repo-provenance.md` for the source snapshot and staleness baseline.

## Legacy tutorial note

The repository still contains older notebook and tutorial material that mentions `Prompter`, `OpenAI`, and `Pipeline`. Those names are archived examples, not the current public API. Use the current task classes and the evaluation helpers documented in the sub-skills.

## When to stop and switch sub-skills

- If the user asks about metrics, dataset loading, or ROUGE, switch to evaluation.
- If the user asks about prompt templates, schema-based outputs, async calls, batch processing, or provider errors, stay in structured-tasks.
- If the user only needs the installation baseline or freshness check, read `references/repo-provenance.md` and the root troubleshooting note.

