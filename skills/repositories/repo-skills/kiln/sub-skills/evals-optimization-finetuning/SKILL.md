---
name: evals-optimization-finetuning
description: "Operate Kiln evals, synthetic data, repair, prompt optimization,
  statistics comparisons, dataset splits, and fine-tuning workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Kiln Evals, Optimization, and Fine-Tuning

Use this sub-skill when the task is about Kiln evaluators, G-Eval or LLM-as-judge runs, eval score summaries, synthetic data generation, task Data Guides, repair, prompt optimization jobs, dataset splits, fine-tune dataset export, or fine-tune provider jobs.

## Route first

- Use this sub-skill for `Eval`, `EvalConfig`, `EvalRun`, `EvalRunner`, G-Eval, LLM-as-judge, eval calibration, run-config comparison summaries, `/api/statistics`, synthetic data topics/inputs/outputs, DataGuide preview/refine/save, repair task inputs, `PromptOptimizationJob`, `DatasetSplit`, fine-tune dataset formatting, fine-tune provider adapters, fine-tune run-config IDs, and fine-tune status handling.
- Route base project/task/run/prompt persistence, `.kiln` save/load mechanics, parent paths, and package-project basics to the project-datamodel sub-skill.
- Route model/provider primitives, `adapter_for_task`, run config fields, prompts, tools, skills, MCP, Ollama, and provider credential setup to the task-execution-providers-tools sub-skill. This sub-skill only explains how those primitives are used inside eval/data-generation/optimization/fine-tune workflows.
- Route RAG document ingestion, extraction, chunking, embeddings, vector stores, and RAG tool setup to the rag-documents-data sub-skill. This sub-skill only covers RAG-related eval or synthetic Q&A generation once documents and tools already exist.
- Route server route wiring, desktop UI route implementation, Svelte components, OpenAPI generation, and app/server build details to the server-desktop-web-api sub-skill.

## Load the right reference

- For evaluator datamodels, G-Eval execution, score summaries, human calibration, and statistical comparisons, read [references/eval-and-statistics.md](references/eval-and-statistics.md).
- For synthetic data topic/input/output generation, Data Guides, Q&A generation, and repair, read [references/synthetic-data-and-repair.md](references/synthetic-data-and-repair.md).
- For Kiln Copilot prompt optimization jobs and the generated prompt/run-config artifacts, read [references/prompt-optimization.md](references/prompt-optimization.md).
- For dataset splits, fine-tune datamodels, dataset JSONL formats, adapters, provider boundaries, and status/update behavior, read [references/fine-tuning.md](references/fine-tuning.md).
- For common failures and recovery paths across these workflows, read [references/troubleshooting.md](references/troubleshooting.md).

## Safe bundled script

Use `scripts/validate_finetune_dataset.py` to validate small local JSONL-style fine-tune datasets without importing Kiln and without calling any provider:

```bash
python scripts/validate_finetune_dataset.py path/to/train.jsonl
python scripts/validate_finetune_dataset.py path/to/train.jsonl --format openai-chat --expect-structured-output
python scripts/validate_finetune_dataset.py path/to/train.jsonl --format vertex-gemini --require-tools --summary-json
```

The script checks JSONL shape, chat/message roles, optional tool-call consistency, optional structured final outputs, optional thinking markers, and UTF-8/JSON parse errors. It does not validate provider eligibility, upload to a provider, call model APIs, read Kiln projects, or modify files.

## Evidence notes

This sub-skill is distilled from repo-relative evidence in `libs/core/kiln_ai/datamodel/eval.py`, `libs/core/kiln_ai/datamodel/spec.py`, `libs/core/kiln_ai/datamodel/data_guide.py`, `libs/core/kiln_ai/datamodel/prompt_optimization_job.py`, `libs/core/kiln_ai/datamodel/finetune.py`, `libs/core/kiln_ai/datamodel/dataset_split.py`, `libs/core/kiln_ai/adapters/eval/`, `libs/core/kiln_ai/adapters/data_gen/`, `libs/core/kiln_ai/adapters/repair/`, `libs/core/kiln_ai/adapters/fine_tune/`, `libs/server/kiln_server/statistics_api.py`, `libs/server/kiln_server/statistics_lib.py`, `app/desktop/studio_server/eval_api.py`, `app/desktop/studio_server/data_gen_api.py`, `app/desktop/studio_server/prompt_optimization_job_api.py`, `app/desktop/studio_server/finetune_api.py`, and associated tests. Verified package evidence covered `kiln-ai`, `kiln-server`, and `kiln-studio-desktop` 1.0.4.
