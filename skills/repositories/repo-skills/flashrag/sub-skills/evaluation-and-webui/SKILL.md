---
name: evaluation-and-webui
description: "Configure and troubleshoot FlashRAG evaluation metrics, prediction
  parsing, result validation, and WebUI/chat/evaluate setup without launching
  services by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# FlashRAG Evaluation and WebUI

Use this sub-skill when the task is about FlashRAG evaluation scores, metric selection, parsed predictions, evaluation output validation, or WebUI chat/evaluate configuration triage.

## Route by Task

- **Evaluation metrics**: Use `references/evaluation-api.md` to choose `metrics`, fill `metric_setting`, understand output keys, and validate `Evaluator` behavior.
- **Prediction parsing**: Use `references/evaluation-api.md` before scoring outputs from SelfAsk, IRCoT, first-line answers, or Gaokao multiple-choice generations.
- **WebUI setup triage**: Use `references/webui.md` to inspect Gradio UI modules, saved YAML configs, chat/evaluate inputs, and index/model configuration requirements.
- **Failure diagnosis**: Use `references/troubleshooting.md` for missing metric packages, Chinese/English metric mismatches, LLMJudge setup, malformed predictions, WebUI imports, and port/service caveats.
- **Metric inventory**: Run `skills/flashrag/sub-skills/evaluation-and-webui/scripts/inspect_metrics.py` against an installed or source checkout to list implemented metric classes without launching generators, retrievers, or WebUI services.

## Safe Defaults

- Do not launch the WebUI, start model servers, call external APIs, or load large models unless the user explicitly asks.
- Prefer static inspection, config preview, and small dataset/sample checks before full evaluation.
- Keep evaluation responsibilities separate from data/config setup, pipeline execution, and model backend selection; route those to the corresponding FlashRAG sub-skills.

## Minimal Evaluation Checklist

1. Confirm dataset objects contain the fields required by selected metrics: usually `pred`, `golden_answers`, `choices`, and optionally `retrieval_result`, `prompt`, `question`, `subject`, or `question_type`.
2. Ensure `metrics` names match implemented `metric_name` values, lowercased by `Evaluator`.
3. Fill `metric_setting` for metrics that require it, especially retrieval top-k, BLEU options, tokenizers, or LLMJudge settings.
4. Apply the correct prediction parser before exact-match style metrics when a pipeline emits reasoning plus a final answer.
5. Validate both aggregate result keys and per-item evaluation scores when `save_intermediate_data` is enabled.

## References and Scripts

- `references/evaluation-api.md` — evaluator lifecycle, available metrics, parser behavior, metric config, and validation patterns.
- `references/webui.md` — WebUI module map, chat/evaluate flow, config save/load, and non-launch triage steps.
- `references/troubleshooting.md` — targeted fixes for dependency, metric, prediction, and WebUI failures.
- `scripts/inspect_metrics.py` — bundled at `skills/flashrag/sub-skills/evaluation-and-webui/scripts/inspect_metrics.py`; static AST metric lister with optional safe import mode.
