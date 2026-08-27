---
name: modeling-and-evaluation
description: "Use for H2O LLM Studio model wrappers, losses, metrics, evaluation
  outputs, inference routing, plots, and AI-judge metric behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# H2O LLM Studio modeling and evaluation

Use this sub-skill when the task is about how H2O LLM Studio maps a problem type to model wrappers, losses, metrics, inference behavior, generated prediction outputs, validation plots, or AI-judge metrics.

Do **not** use this sub-skill for:

- creating or repairing experiment YAML/data schemas: use `configuration-and-data`;
- launching, scheduling, or debugging training runs: use `training-and-experiments`;
- interactive chat, model-card export, or Hugging Face publishing: use `export-and-prompt`.

## Operating workflow

1. Identify the `problem_type` first. Valid modeling/evaluation problem types are:
   `text_causal_language_modeling`, `text_sequence_to_sequence_modeling`,
   `text_dpo_modeling`, `text_causal_classification_modeling`, and
   `text_causal_regression_modeling`.
2. Load [references/model-and-metric-reference.md](references/model-and-metric-reference.md) for class mappings, forward/generate contracts, losses, metric direction, and expected result keys.
3. Load [references/evaluation-workflows.md](references/evaluation-workflows.md) for `run_inference`, `run_eval`, prediction files, plot files, generation-vs-forward routing, and GPT/MT-Bench judge behavior.
4. For unsupported metrics, NaNs, empty outputs, OpenAI/Azure endpoint issues, missing `prompts/`, or classification/regression shape errors, load [references/troubleshooting.md](references/troubleshooting.md).
5. Use [scripts/inspect_problem_type.py](scripts/inspect_problem_type.py) for a safe local inspection that lists the configured model/loss/metric/plot classes without instantiating or downloading a model.

## Quick commands

```bash
python scripts/inspect_problem_type.py --problem-type text_causal_classification_modeling --list-metrics
python scripts/inspect_problem_type.py --problem-type all --json
python scripts/inspect_problem_type.py --problem-type text_dpo_modeling --verify-imports
```

The inspection script is safe by default: it prints static and import-level metadata only. It does not start training, call an AI judge, load Hugging Face weights, or create model instances.

## Decision rules

- For generative validation metrics other than `Perplexity`, causal LM, sequence-to-sequence, and DPO use generation; `Perplexity` uses a forward pass.
- Classification and regression are non-generation tasks. They always use a forward pass and postprocess logits or regression head outputs into predictions before metrics are computed.
- `GPT` metrics call an OpenAI-compatible Chat Completions endpoint and can incur network cost. Require endpoint, credential, and budget confirmation before running; use static reasoning or mocked tests when possible.
- Validation artifacts are written by the training/evaluation workflow, not by the model classes themselves. Expect raw prediction pickle, prediction CSV, and parquet plot data when evaluation reaches rank 0 successfully.
