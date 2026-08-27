---
name: evaluation
description: "Run and troubleshoot VLMEvalKit evaluations, result reuse, async
  API mode, and run summaries."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# evaluation

Use this sub-skill when a task is to run, resume, inspect, summarize, or troubleshoot VLMEvalKit evaluations through `run.py` or `vlmutil`.

## Route first

- Build safe `run.py` and `vlmutil` commands with [CLI reference](references/cli-reference.md).
- Choose an execution pattern for image, video, multi-turn, local/API, inference-only, eval-only, async API, and reuse runs with [workflows](references/workflows.md).
- Interpret outputs, `status.json`, symlinked latest files, checkpoints, summaries, and failure scans with [results and status](references/results-and-status.md).
- Diagnose common failures with [troubleshooting](references/troubleshooting.md).
- Use [scripts/run_torchrun.sh](scripts/run_torchrun.sh) only when GPUs are intentionally visible and `torchrun` is desired.
- Use [scripts/scan_api_failures.py](scripts/scan_api_failures.py) to inspect prediction/evaluation files without depending on the source checkout.
- Use [scripts/summarize_runs.py](scripts/summarize_runs.py) to summarize one or more VLMEvalKit `status.json` run directories.

## Handle here

- `python run.py --data ... --model ...` and `python run.py --config ...` command construction.
- `--mode all|infer|eval`, `--work-dir`, `--api-nproc`, `--retry`, `--keep-failed`, `--reuse`, and `--reuse-aux` decisions.
- OpenAI-compatible evaluation commands using `--base-url`, `--key`, `--custom-prompt`, `--video-llm`, `--local-media`, `--stream`, `--api-mode`, and `--monitor-interval`.
- Judge configuration with `--judge`, `--judge-args`, `--judge-base-url`, `--judge-key`, `--judge-api-nproc`, `--judge-retry`, and `--judge-timeout`.
- Result reuse, missing/failed prediction triage, run summaries, and utility/result scans.
- Environment knobs that affect evaluation outputs: `PRED_FORMAT`, `EVAL_FORMAT`, `SPLIT_THINK`, `SKIP_ERR`, `MMEVAL_ROOT`, `EVAL_PROXY`, `LOCAL_LLM`, `FWD_API`, `LMUData`, and `VLMEVALKIT_USE_MODELSCOPE`.

## Route elsewhere

- Implementing or changing model/API wrappers, prompt adapters, LiteLLM/LMDeploy provider classes, or `supported_VLM` entries: use [../model-development/SKILL.md](../model-development/SKILL.md).
- Implementing or changing benchmarks, dataset converters, TSV schemas, `build_prompt`, or `evaluate`: use [../benchmark-authoring/SKILL.md](../benchmark-authoring/SKILL.md).

## Verification boundary

Skill construction used `README.md`, `docs/en/Quickstart.md`, `docs/en/ConfigSystem.md`, `docs/en/EvalByLMDeploy.md`, `run.py`, `vlmeval/inference.py`, `vlmeval/inference_mt.py`, `vlmeval/inference_video.py`, `vlmeval/inference_api.py`, `vlmeval/tools.py`, `vlmeval/smp/file.py`, `vlmeval/smp/status_report.py`, `tests/test_inference_api.py`, and selected source scripts as evidence. Inspection verified package import/CLI surfaces and lightweight native API-pipeline checks. It did not verify live provider API calls, dataset downloads, Gradio services, or large GPU model evaluations.
