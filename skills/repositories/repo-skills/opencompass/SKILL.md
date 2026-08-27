---
name: opencompass
description: "Use OpenCompass to configure, run, debug, and analyze large-model
  evaluations across CLI/config workflows, datasets, model backends, prompts,
  inferencers, summarizers, and LLM-as-judge results."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenCompass

Use this skill when a task involves OpenCompass, the `opencompass` Python package/CLI, or OpenCompass-style LLM evaluation configs, datasets, model adapters, prompts, backends, or result summaries.

## First Checks

- Verify the package imports with `python -c "import opencompass; print(opencompass.__version__)"`.
- Verify the CLI exists with `opencompass --help` before proposing launch commands.
- Use `opencompass path/to/config.py --dry-run` for task planning and `--debug` for a first sequential execution.
- Treat optional extras (`full`, `api`, `lmdeploy`, `vllm`) as workflow-specific installs, not default requirements for every task.
- Never put API keys, private model tokens, cluster credentials, or judge credentials into reusable configs or skill artifacts.

## Route by Scenario

- **Run or resume evaluations**: use `sub-skills/evaluation-workflows/SKILL.md` for CLI launch commands, `--mode`, `--debug`, `--dry-run`, `--reuse`, `--work-dir`, local/Slurm/DLC runners, and partitioners.
- **Author configs or datasets**: use `sub-skills/configuration-and-datasets/SKILL.md` for `read_base()`, built-in config selection, `models`/`datasets`/`summarizer`, `CustomDataset`, local JSONL/CSV, and dataset source mappings.
- **Configure models/backends**: use `sub-skills/model-backends/SKILL.md` for HuggingFace, API providers, custom models, LMDeploy, vLLM, accelerator flags, resource `run_cfg`, tokenizer kwargs, and credential-safe checks.
- **Debug prompts/inference configs**: use `sub-skills/prompt-and-inference/SKILL.md` for `PromptTemplate`, dialogue `PromptList`, `meta_template`, retrievers, `GenInferencer`, `PPLInferencer`, and answer masking.
- **Analyze outputs**: use `sub-skills/results-and-analysis/SKILL.md` for summary tables, `summary_groups`, result files, `GenericLLMEvaluator`, subjective evaluation, repeat analysis, and result-station behavior.

## Shared References

- `references/installation-and-extras.md`: install variants, optional extras, minimal verification, and backend-specific dependency boundaries.
- `references/troubleshooting.md`: cross-cutting install/import, CLI, config, backend, data, judge, and result-analysis failures.
- `references/repo-provenance.md`: source baseline, version, dirty-state note, and evidence paths for future refresh decisions.
- `scripts/opencompass_environment_check.py`: safe environment check for package import, distribution metadata, CLI help, and selected optional modules.

## Common Workflows

### Smoke-check an Environment

```bash
python scripts/opencompass_environment_check.py
opencompass --help
```

If the check fails on optional modules, route to the relevant backend/dataset workflow instead of installing every extra.

### Plan a New Evaluation

1. Use `configuration-and-datasets` to assemble or inspect `models`, `datasets`, and optional `summarizer`.
2. Use `model-backends` to validate backend/resource/credential assumptions.
3. Use `prompt-and-inference` when custom `infer_cfg` or prompt behavior matters.
4. Use `evaluation-workflows` to run `--dry-run`, then `--debug`, then the full `--mode all` run.
5. Use `results-and-analysis` to interpret `summary/`, `results/`, and judge outputs.

### Recover a Failed Run

- If inference predictions exist, rerun evaluation with `opencompass config.py --mode eval --reuse -w outputs/run`.
- If evaluation results exist but summaries are missing, rerun visualization with `--mode viz --reuse`.
- If the config changed between runs, compare model/dataset abbreviations and result versions before reusing outputs.

## Safety and Scope

- This skill is self-contained; do not rely on original repository docs, tools, examples, or tests at runtime.
- Do not claim large model, API, vLLM, LMDeploy, Slurm, DLC, or CUDA execution is verified unless the target environment actually runs that workflow.
- Prefer tiny fixtures, CLI help, config parsing, and dry-run checks before any network, model download, GPU job, or credential-bound action.
- Keep root guidance router-like; read the nearest sub-skill references for API tables, config examples, scripts, and troubleshooting details.
