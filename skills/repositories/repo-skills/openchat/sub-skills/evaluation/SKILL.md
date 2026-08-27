---
name: evaluation
description: "Use OpenChat's benchmark harness, answer matchers, and HumanEval
  EvalPlus conversion safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenChat Evaluation

Use this sub-skill when the task is to run or explain OpenChat's bundled benchmark harness, prepare compatible evaluation data, inspect answer-matcher outputs, resume a partial evaluation, or convert `coding/humaneval` results into EvalPlus-compatible samples.

## Read first

- Benchmark workflow and CLI selection: [references/evaluation-workflows.md](references/evaluation-workflows.md)
- Evaluation data layout and supported task families: [references/eval-data-layout.md](references/eval-data-layout.md)
- Failure modes and safe checks: [references/troubleshooting.md](references/troubleshooting.md)

## Use the bundled scripts

- `scripts/run_eval.sh`: thin wrapper around `python -m ochat.evaluation.run_eval`; forwards all arguments and shows upstream `--help`.
- `scripts/check_answer_matchers.py`: small synthetic parser checks for multiple-choice, GSM8K numeric extraction, and HumanEval code extraction.
- `scripts/convert_to_evalplus.py`: converts OpenChat result JSON files containing `coding/humaneval` rows into EvalPlus JSONL sample files.

## Route boundaries

- Prompt-template internals, C-RLFT condition formatting, tokenizer chat templates, and model-type template details belong in [`../prompting/`](../prompting/).
- OpenAI-compatible API server deployment, vLLM server flags, Docker deployment evidence, and request serving belong in [`../serving/`](../serving/).
- `conv_eval.py`, MT-Bench, Vicuna Bench, and AlpacaEval orchestration are reference-only for this sub-skill because they require external benchmark repositories and long-running services.

## Operating reminders

1. Do not assume a package checkout or bundled `eval_data` directory exists. Ask the user to provide a local evaluation data directory following [the documented layout](references/eval-data-layout.md).
2. Choose the execution path before running: non-GPT model identifiers use local vLLM; model names beginning with `gpt-3.5-turbo` or `gpt-4` use the OpenAI API client.
3. Treat parser checks as quick smoke tests only. They do not load model weights, call an API, or execute HumanEval code.
4. Treat benchmark runs as potentially expensive: local vLLM requires model weights and GPU memory; the OpenAI path requires credentials, network access, and API quota.
5. For coding/HumanEval, OpenChat extracts code samples; correctness is established by an external EvalPlus run, not by OpenChat's `is_correct` field.
