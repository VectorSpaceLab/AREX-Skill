# Cross-Cutting Troubleshooting

## Install And Import

- Symptom: `ModuleNotFoundError: lm_eval` or `lm-eval: command not found`.
  - Cause: package is not installed in the active Python environment or console scripts are not on `PATH`.
  - Next step: install the package, then run `python -m lm_eval --help` and `lm-eval --help`.
- Symptom: base package imports, but backend modules fail with missing `torch`, `transformers`, `vllm`, `litellm`, or service SDKs.
  - Cause: model backends are optional extras.
  - Next step: route to `sub-skills/model-backends/` and install only the extra needed for the selected backend.

## CLI And Config

- Symptom: a command copied from older docs fails because it omits `run`.
  - Cause: this checkout supports legacy mapping, but explicit `lm-eval run ...` is clearer and safer.
  - Next step: route to `sub-skills/evaluation-runs/`.
- Symptom: config file values are ignored.
  - Cause: CLI args override YAML config values.
  - Next step: inspect effective config through the evaluation-runs reference and avoid duplicate settings.

## Tasks And Data

- Symptom: task is missing or a custom task cannot be found.
  - Cause: task name typo, group/tag confusion, or missing `--include_path`.
  - Next step: route to `sub-skills/task-authoring/`; use listing and static YAML checks before running downloads.
- Symptom: validation would execute untrusted Python or dataset loading code.
  - Cause: `!function`, local loading scripts, or unsafe-code tasks.
  - Next step: ask for explicit approval before runtime validation or full evaluation.

## Results And Logging

- Symptom: `--log_samples` produces no useful saved samples.
  - Cause: missing or unsuitable `--output_path`.
  - Next step: route to `sub-skills/result-logging/` and set local output paths before any external upload.
- Symptom: W&B, Trackio, Hugging Face Hub, or Zeno upload fails.
  - Cause: optional dependency, credential, network, or repository permission issue.
  - Next step: keep results local unless the user explicitly approves upload and secret handling.

## Decontamination And Maintenance

- Symptom: user asks to run clean-training-data scripts immediately.
  - Cause: the upstream decontamination data pipeline is multi-day and large-data dependent.
  - Next step: route to `sub-skills/decontamination-maintenance/` for static review and safety classification.
