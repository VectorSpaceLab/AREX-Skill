---
name: skywork-r1v
description: "Route Skywork-R1V3 local inference, R1V4 API batch testing, and
  benchmark reproduction workflows to the right bundled sub-skill."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Skywork-R1V

Use this repo skill when a user asks about the Skywork multimodal reasoning repository, especially Skywork-R1V3 local inference, Skywork R1V4 API batch testing, or evaluation reproduction with VLMEvalKit, EMMA-mini, and MMK12.

This root skill is a router. It keeps the fast path short and sends detailed commands, parameters, and failure handling to the sub-skill that owns the workflow.

## First choices

- Need local Transformers or vLLM inference for Skywork-R1V3? Go to `sub-skills/local-inference/`.
- Need R1V4 batch request payloads, response parsing, or result summaries? Go to `sub-skills/r1v4-api-testing/`.
- Need Skywork evaluation reproduction, benchmark launch commands, or score post-processing? Go to `sub-skills/evaluation-reproduction/`.

## What this skill covers

- Skywork-R1V3 local inference command construction and image-patch reasoning.
- Skywork R1V4 API batch testing and tagged response parsing.
- VLMEvalKit, EMMA-mini, and MMK12 evaluation reproduction.
- Safe helper scripts for command building, schema checks, parsing, and output inspection.

## What this skill does not do

- It does not load the 38B model, launch vLLM, or run the heavy evaluation suites by itself.
- It does not make live API calls, download checkpoints, or request credentials unless the chosen sub-skill says so.
- It does not replace the need for a prepared CUDA/GPU runtime when the user is actually running local inference.

## Minimal setup and sanity check

There is no single top-level Python package to install for this repository. For the bundled helper scripts, use a normal Python environment and install only the small helper stack when needed:

```bash
python -m pip install requests tqdm flask pillow pyyaml pandas openpyxl
python scripts/validate_skill_runtime.py --root .
```

Install CUDA, vLLM, Transformers, model weights, datasets, or judge/API clients only when the chosen sub-skill explicitly requires them for a real run.

## Quick routing signals

### Local inference
Use `local-inference` when the request mentions:

- `Skywork/Skywork-R1V3-38B`
- `inference_with_transformers.py`
- `inference_with_vllm.py`
- `split_model`, `tensor_parallel_size`, `flash-attn`, `trust_remote_code`
- multi-image prompts, image patch counts, or CUDA OOM while serving the model

Read:

- `sub-skills/local-inference/references/workflows.md`
- `sub-skills/local-inference/references/api-and-parameters.md`
- `sub-skills/local-inference/references/troubleshooting.md`

Run:

- `sub-skills/local-inference/scripts/build_inference_command.py`
- `sub-skills/local-inference/scripts/check_image_grid.py`

### R1V4 API testing
Use `r1v4-api-testing` when the request mentions:

- `r1v4-lite` or `r1v4-vl-planner-lite`
- `batch_nonstream.py`, `batch_stream.py`, or planner variants
- `test_cases.jsonl`, `<think>`, `<tool_call>`, `<observation>`, `<answer>` tags
- result JSONL summaries, MIME types, or a safe batch payload preview

Read:

- `sub-skills/r1v4-api-testing/references/api-batch-workflows.md`
- `sub-skills/r1v4-api-testing/references/data-formats.md`
- `sub-skills/r1v4-api-testing/references/result-analysis.md`
- `sub-skills/r1v4-api-testing/references/troubleshooting.md`

Run:

- `sub-skills/r1v4-api-testing/scripts/validate_cases.py`
- `sub-skills/r1v4-api-testing/scripts/build_api_payload.py`
- `sub-skills/r1v4-api-testing/scripts/parse_r1v4_response.py`
- `sub-skills/r1v4-api-testing/scripts/summarize_results.py`

### Evaluation reproduction
Use `evaluation-reproduction` when the request mentions:

- `eval/README.md`
- VLMEvalKit launch or benchmark scripts
- EMMA-mini generation and scoring
- MMK12 generation or judge scoring
- `MMMU`, `LogicVista`, `PhyX`, `r1v3-alpha`, `USE_COT`, or a served OpenAI-compatible model

Read:

- `sub-skills/evaluation-reproduction/references/vlmevalkit.md`
- `sub-skills/evaluation-reproduction/references/emma-mmk12.md`
- `sub-skills/evaluation-reproduction/references/data-and-results.md`
- `sub-skills/evaluation-reproduction/references/troubleshooting.md`

Run:

- `sub-skills/evaluation-reproduction/scripts/build_eval_commands.py`
- `sub-skills/evaluation-reproduction/scripts/score_boxed_answers.py`
- `sub-skills/evaluation-reproduction/scripts/check_eval_outputs.py`

## Helper scripts at the root

- `scripts/validate_skill_runtime.py` checks that the generated tree still has the expected router layout and does not contain obvious path leaks.

## Maintenance note

When you need to check whether this skill still matches the current repository state, read `references/repo-provenance.md` first. That file records the source commit and evidence paths used to build the skill.
