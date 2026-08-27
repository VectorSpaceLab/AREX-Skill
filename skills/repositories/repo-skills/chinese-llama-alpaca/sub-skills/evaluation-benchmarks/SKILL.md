---
name: evaluation-benchmarks
description: "Guide Chinese-LLaMA-Alpaca C-Eval evaluation, scored example
  interpretation, and benchmark reporting without overstating results."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation and Benchmarks Router

Use this sub-skill when a user wants to run or interpret C-Eval scoring, inspect the repo's benchmark/example score tables, or understand how the project compared different quantization/model variants. The commands below assume the current working directory is this sub-skill directory.

Do not claim benchmark-quality results without the underlying model, C-Eval data layout, and runtime approval. The example score tables in `examples/` are paired/comparative and should not be treated as absolute accuracy. If the user needs model generation or asset reconstruction first, route to `../model-reconstruction/` or `../inference-deployment/`.

## Fast Route

1. **Check the C-Eval layout first.** Use [`scripts/validate_ceval_layout.py`](scripts/validate_ceval_layout.py) to confirm `dev/`, `val/`, `test/` subject files and CSV columns.
2. **Review the evaluation workflow.** See [`references/ceval-workflow.md`](references/ceval-workflow.md) for flags, data layout, and outputs.
3. **Interpret example score tables cautiously.** See [`references/example-benchmarks.md`](references/example-benchmarks.md) for paired-score caveats and task categories.
4. **Inspect troubleshooting before rerunning a failed benchmark.** See [`references/troubleshooting.md`](references/troubleshooting.md) for data/layout/model/GPU issues.

## Bundled Runtime Files

- [`scripts/ceval/eval.py`](scripts/ceval/eval.py): C-Eval runner with bundled `--data_dir` and `--subject_mapping` support.
- [`scripts/ceval/evaluator.py`](scripts/ceval/evaluator.py): shared evaluator base class.
- [`scripts/ceval/llama_evaluator.py`](scripts/ceval/llama_evaluator.py): LLaMA evaluator with answer extraction logic.
- [`scripts/ceval/subject_mapping.json`](scripts/ceval/subject_mapping.json): subject grouping reference.
- [`scripts/validate_ceval_layout.py`](scripts/validate_ceval_layout.py): safe layout checker for `dev/`, `val/`, and `test/` CSVs.

## Scope Boundaries

- Model serving, generation, and batch prediction belong to `../inference-deployment/`.
- Model reconstruction and tokenizer merging belong to `../model-reconstruction/`.
- Training and data preparation belong to `../training-finetuning/`.
- This sub-skill can help choose between zero-shot/few-shot/constrained decoding for C-Eval, but it does not replace the need for a compatible model and dataset.
