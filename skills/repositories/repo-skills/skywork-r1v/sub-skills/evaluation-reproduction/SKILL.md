---
name: evaluation-reproduction
description: "Construct and troubleshoot Skywork-R1V3 evaluation workflows for
  VLMEvalKit, EMMA-mini, and MMK12, including command building, prerequisites,
  result post-processing, and judge/API failure handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evaluation Reproduction

Use this sub-skill when you need to reproduce, adapt, or troubleshoot Skywork-R1V3 evaluation workflows.

## Route here
- Two-step VLMEvalKit evaluation flow: prepare the environment, then launch the model and run benchmark scripts.
- EMMA-mini response generation plus answer extraction and scoring.
- MMK12 generation plus judge-based Yes/No scoring.
- Safe command building and output inspection for these workflows.

## Do not use this sub-skill for
- User-facing local ad hoc inference or one-off prompts.
- R1V4 API batch testing.
- Generic VLMEvalKit internals that are not customized for Skywork-R1V3.

## Bundled helpers
- [references/vlmevalkit.md](references/vlmevalkit.md)
- [references/emma-mmk12.md](references/emma-mmk12.md)
- [references/data-and-results.md](references/data-and-results.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/build_eval_commands.py](scripts/build_eval_commands.py)
- [scripts/score_boxed_answers.py](scripts/score_boxed_answers.py)
- [scripts/check_eval_outputs.py](scripts/check_eval_outputs.py)

## Safe defaults
- Treat the environment recipe as heavy and explicit; do not run it blindly.
- Keep the vLLM server and client base URL aligned.
- Prefer `USE_COT=1` for the scripted VLMEvalKit Skywork runs unless a dataset-specific rule says otherwise.
- Keep judge keys and base URLs out of runtime files; use environment variables or a local wrapper.
- Normalize math-style answers with the last `\boxed{...}` before judging.

## Handoff shape
- This skill explains command construction, data prerequisites, result checks, and failure handling.
- It does not ship benchmark data, model weights, or credentials.
- If the workflow crosses into another evaluation family, stop and route instead of mixing workflows.
