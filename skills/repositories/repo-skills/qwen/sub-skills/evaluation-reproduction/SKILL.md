---
name: evaluation-reproduction
description: "Route Qwen benchmark reproduction and evaluation-script selection
  for C-Eval, MMLU, CMMLU, GSM8K, HumanEval, and plugin workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qwen Evaluation and Reproduction

Use this sub-skill when the user wants to reproduce Qwen benchmarks, select an evaluation script, prepare data directories, or understand the differences between base and chat evaluation paths.

## Safe start

- Use `scripts/qwen_eval_command_builder.py` to print a benchmark command plan without downloading datasets or loading a model.
- Treat HumanEval execution as sandbox-sensitive. Do not run untrusted generated code without explicit approval.
- Do not assume the chat evaluation scripts reproduce the same protocol as external benchmark harnesses; the repository documentation explicitly notes 0-shot chat results in some places where 5-shot results came from another system.

## Routes

| User request | Read |
| --- | --- |
| C-Eval, MMLU, CMMLU, GSM8K, HumanEval, or plugin benchmark overview and file layout | `references/benchmark-reproduction.md` |
| Script flags, model/checkpoint selection, dataset arguments, and base-vs-chat command differences | `references/evaluation-script-reference.md` |
| Missing dataset, wrong result path, sandbox concern, or benchmark dependency issue | `references/troubleshooting.md` |

## Boundaries

- For inference of the underlying checkpoint, use `../inference-model-loading/SKILL.md`.
- For prompt/tool-use behavior, use `../prompting-tool-use-tokenization/SKILL.md`.
- For serving or deployment, use `../serving-deployment/SKILL.md`.
- For finetuning or quantization, use `../finetuning-quantization/SKILL.md`.

## Operating rules

- Benchmark commands are only useful when the dataset layout, checkpoint family, and seed are explicit.
- Never present a score without the benchmark dataset and result file locations the repo expects.
- Keep the repository's warning about HumanEval untrusted code execution visible.
