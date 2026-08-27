---
name: evaluation-workflows
description: "Run, resume, dry-run, and debug OpenCompass evaluation jobs from
  the installed opencompass CLI or config-defined runner workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation Workflows

Use this sub-skill when an agent needs to launch or debug OpenCompass evaluation execution: planning a run, choosing `--mode`, using `--debug` or `--dry-run`, resuming with `--reuse`, selecting local/Slurm/DLC orchestration, or checking whether the installed CLI is available.

## Route Here For

- Running `opencompass` from a config file or from `--models` / `--datasets` shortcuts.
- Safe first-run checks with `--debug`, `--dry-run`, explicit `--work-dir`, and small dataset/model selections.
- Resuming a failed run from a previous `work_dir` timestamp with `--mode eval`, `--mode viz`, and `--reuse`.
- Choosing local, Slurm, or DLC execution and understanding how partitioners produce tasks for runners.
- Creating native verification candidates that exercise CLI construction without requiring model downloads, GPU execution, or credentials.

## Route Elsewhere

- Config inheritance, model/dataset lists, custom datasets, and config authoring belong in `../configuration-and-datasets/SKILL.md`.
- HuggingFace/API/vLLM/LMDeploy adapter details and backend installation choices belong in `../model-backends/SKILL.md`.
- Prompt templates, retrievers, inferencers, and OpenICL internals belong in `../prompt-and-inference/SKILL.md`.
- Summarizer customization, result table interpretation, and repeat-analysis outputs belong in `../results-and-analysis/SKILL.md`.

## Start Here

1. Prefer the installed CLI entrypoint: `opencompass`, not a source-checkout script dependency.
2. For a new config, start with a sequential sanity run: `opencompass path/to/eval_config.py --debug -w outputs/smoke`.
3. To inspect task planning without running model jobs, add `--dry-run`; this implies debug behavior and returns before runner execution.
4. For a complete run, use `opencompass path/to/eval_config.py -w outputs/experiment --mode all`.
5. If inference already exists, rerun downstream stages with `--mode eval --reuse` or `--mode viz --reuse` and the same `--work-dir`.

## References

- `references/cli-workflows.md`: command patterns for configure -> inference -> evaluation -> visualization, dry runs, debug runs, reuse, and work directory handling.
- `references/runners-and-partitioners.md`: how local, Slurm, and DLC runners interact with partitioners and task types.
- `references/troubleshooting.md`: common execution failures and safe diagnosis steps.
- `scripts/opencompass_cli_smoke.py`: safe CLI help/argument smoke check that does not run models.

## Safety Notes

- Do not claim that real HuggingFace model inference was verified unless the target environment has compatible model/runtime dependencies and the run actually completed.
- Optional execution backends such as vLLM, LMDeploy, DLC, and API extras may require additional packages or credentials; keep those checks separate from CLI smoke validation.
- Treat `--hf-num-gpus` as the minimum required GPU count used for scheduling/allocation, not as proof that OpenCompass will consume exactly that many GPUs.
