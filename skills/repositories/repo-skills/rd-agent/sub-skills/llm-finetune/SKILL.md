---
name: llm-finetune
description: "Operate RD-Agent FT-Agent workflows for benchmark-driven LLM data
  processing, fine-tuning, merge, evaluation, and feedback loops."
metadata:
  disco-role: operating
  parent-skill: rd-agent
license: MIT
disable-model-invocation: true
---

# RD-Agent LLM fine-tuning

Use this sub-skill for `rdagent llm_finetune`, FT-Agent datasets/benchmarks, LLaMA-Factory training configuration, OpenCompass evaluation, batch jobs, and the fine-tune UI.

## Prerequisites and cost gate

A realistic run can download models and datasets, call an LLM provider, start Docker or conda training environments, and consume GPU hours. Before running, confirm Linux, a usable Docker/conda backend, NVIDIA/CUDA capacity when required, Hugging Face access, provider credentials, and a stable `FT_FILE_PATH`. A missing prerequisite is a blocked run, not a reason to substitute a toy score.

Keep the main settings explicit and secret-free in the shell or a private `.env`:

```text
BACKEND
CHAT_MODEL
OPENAI_API_KEY / OPENAI_API_BASE
EMBEDDING_MODEL
FT_FILE_PATH
FT_Coder_CoSTEER_env_type=docker|conda
FT_TARGET_BENCHMARK
FT_BENCHMARK_DESCRIPTION
FT_BASE_MODEL
FT_UPPER_DATA_SIZE_LIMIT
FT_API_MAX_WORKERS
FT_STRONG_MODELS / FT_WEAK_MODELS
HF_TOKEN (only when required)
```

Use [validate_ft_env.py](scripts/validate_ft_env.py) to print presence only; it never prints values.

## Single-task workflow

Start with help and a bounded configuration:

```bash
rdagent llm_finetune --help
rdagent llm_finetune \
  --benchmark <benchmark> \
  --benchmark-description "<task and output format>" \
  --base-model <huggingface-model-id> \
  --loop-n 1 \
  --timeout <short-budget>
```

The checked-in implementation follows this progression:

1. inspect the benchmark and registered raw datasets;
2. generate data-processing code and a training config;
3. fail fast on schema/config/runtime errors;
4. fine-tune the target model;
5. evaluate with the configured evaluation stack;
6. feed validation feedback into the next iteration while keeping test results for final reporting.

The `--dataset` option selects the agent's dataset after registered resources are prepared; it does not necessarily avoid initial dataset preparation. Reuse a stable `FT_FILE_PATH` when intentionally caching assets.

## Batch jobs and UI

For repeatable multi-task runs, copy the checked-in task template to a private file, copy the private `.env` into the job directory, and run the bundled job shell script only after inspecting its commands. The Streamlit fine-tune UI is a reporting/interaction surface, not proof that training or evaluation succeeded. Preserve training config, dataset schema, checkpoint path, merge/evaluation output, and validation metric.

## Failure boundaries

- dataset/download/license failure → data/provider block;
- generated data schema failure → fix processing before training;
- Docker/CUDA/model-load failure → backend block;
- training completes but evaluation cannot consume the checkpoint → artifact/evaluator failure;
- provider quota or context failure → provider failure, not a model-quality result.

Read [fine-tune-contract.md](references/fine-tune-contract.md) before a costly run and the parent troubleshooting guide for recovery.
