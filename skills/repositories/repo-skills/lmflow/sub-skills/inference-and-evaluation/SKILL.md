---
name: inference-and-evaluation
description: "Helps with LMFlow generation, evaluation, benchmark, and optional
  vLLM or SGLang inference workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference and Evaluation

Use this sub-skill when the task is about generating text with LMFlow, running evaluator/benchmark flows, handling inference results, or choosing between the Hugging Face, vLLM, and SGLang routes.

## Typical Triggers

- `inference`, `generate`, `chat`, `tool inference`, `speculative inference`
- `evaluator`, `benchmarking`, `metric`, `answer extraction`
- `vllm`, `sglang`, `save_inference_results`, `results_path`
- `reward model inference`, `text_regression`, `DataProto`

## What This Sub-Skill Owns

- Batch generation and evaluation commands built from the installed LMFlow package.
- Engine selection for Hugging Face, vLLM, and SGLang.
- Result-format guidance, save/load paths, and DataProto usage.
- Safe command rendering for non-training inference and evaluation.

## Read These First

- `references/workflows.md` for the supported inference and evaluation paths.
- `references/cli-reference.md` for the important generation/evaluation dataclass fields.
- `references/results-and-dataproto.md` for result objects and output files.
- `references/troubleshooting.md` for deepspeed, engine, and result-path issues.
- `scripts/build_inference_command.py` to render a copyable command.

## Cross-Links

- Dataset preparation lives in `../data-and-templates/SKILL.md`.
- Fine-tuning lives in `../training-and-optimization/SKILL.md`.
- Reward-modeling and DPO workflows live in `../post-training-alignment/SKILL.md`.

## Workflow

1. Decide whether the user wants plain generation, evaluation, or a backend engine.
2. Confirm the dataset path and model path.
3. Decide whether outputs should be printed, saved, or both.
4. Check whether the task needs `vllm` or `sglang` and whether those extras are installed in a separate environment.
5. Render the command before running anything expensive.

## Common Decisions

- Use Hugging Face inference for the simplest path and base-install compatibility.
- Use vLLM only when the user explicitly wants vLLM and has that extra installed.
- Use SGLang only when the user explicitly wants SGLang, deterministic inference, or return-logprob behavior.
- Use the evaluator path when the user asks for metrics rather than raw generations.

## What Not To Do

- Do not mix vLLM and SGLang dependency assumptions.
- Do not hide `save_inference_results` output paths.
- Do not promise `return_logprob` unless the route is SGLang.
- Do not route training tasks here.
