---
name: react-inference
description: "Configure, validate, and troubleshoot Tongyi DeepResearch ReAct
  inference workflows, data, tools, and rollout outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# React Inference

Use this sub-skill when a user needs to set up, inspect, or troubleshoot Tongyi DeepResearch ReAct inference: `.env` values, JSON/JSONL input data, file references, local vLLM serving, OpenRouter or other OpenAI-compatible adaptation, rollout arguments, ReAct loop behavior, and tool contracts.

Do not use this sub-skill for benchmark judging or metric aggregation; route that to `benchmark-evaluation`. Do not use it to choose among WebAgent-family projects; route that to `webagent-family`. Do not run full local inference unless the user has explicitly provided model weights, GPUs, service credentials, and runtime approval.

## Operating Procedure

1. **Classify the route.**
   - Local vLLM route: the repository launcher expects a local model path, eight visible CUDA devices, ports `6001` through `6008`, and a `.env` file.
   - OpenRouter/OpenAI-compatible route: future agents must adapt the ReAct model call in the working copy to the provider base URL, API key, model id, and reasoning-content concatenation convention; do not run the eight-port launcher for this route.
2. **Preflight configuration.** Use `scripts/build_react_env.py` to print a safe template, generate an `.env`, or validate one. Treat `MODEL_PATH`, `DATASET`, and `OUTPUT_PATH` as strict fields. Treat Serper, Jina, summary API, Dashscope, and SandboxFusion credentials as required only when the corresponding tool is enabled or likely to be called.
3. **Preflight input data.** Use `scripts/validate_deepresearch_dataset.py` on JSON/JSONL files. If questions contain uploaded-file markers, supply the matching `file_corpus` directory and verify that all referenced files are present.
4. **Explain execution shape before launching.** The launcher loads `.env`, validates `MODEL_PATH`, starts eight vLLM servers, waits for `/v1/models` readiness, then runs `run_multi_react.py` with rollout, split, worker, model, and sampling arguments.
5. **Reason from the ReAct transcript.** Model messages alternate assistant output with `<tool_call>...</tool_call>` and user `<tool_response>...</tool_response>`. A valid final answer must be enclosed in `<answer>...</answer>`.
6. **Troubleshoot by layer.** Check configuration, dataset shape, model serving, external service credentials, tool-call JSON, file-corpus placement, token/time limits, and missing `<answer>` termination in that order.

## Bundled References

- `references/workflows.md` — local vLLM and OpenAI-compatible routes, `.env` variables, launcher behavior, `run_multi_react.py` arguments, output layout, and ReAct loop.
- `references/data-formats.md` — JSON/JSONL input records, file references, file-corpus placement, and rollout output fields.
- `references/tool-contracts.md` — `search`, `visit`, `google_scholar`, `PythonInterpreter`, and `parse_file` contracts and credentials.
- `references/troubleshooting.md` — symptom-driven checks for common setup, runtime, and ReAct termination failures.

## Bundled Scripts

- `scripts/build_react_env.py --help` — stdlib helper to generate or validate a DeepResearch-style `.env` without secrets or network calls.
- `scripts/validate_deepresearch_dataset.py --help` — stdlib helper to validate question/answer JSON or JSONL records and uploaded-file references.

## Evidence Basis

This sub-skill distills the repository README, FAQ, environment example, requirements list, ReAct launcher, rollout runner, agent loop, prompt/tool sources, and the provided example JSONL/file-corpus fixtures. It is self-contained; future agents should not need to reopen those source files for routine inference setup questions.
