---
name: vlm-eval-kit
description: "Use VLMEvalKit (`vlmeval`) for vision-language model evaluation,
  model/API configuration, benchmark authoring, result inspection, and
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# VLMEvalKit (`vlmeval`)

Use this repo skill when a task involves VLMEvalKit, the `vlmeval` Python package, OpenCompass multimodal/VLM evaluation workflows, supported VLM/API model names, benchmark datasets, `run.py`, `vlmutil`, `LMUData`, prediction/result files, or VLMEvalKit-specific errors.

VLMEvalKit is an evaluation toolkit for large vision-language models. It provides one-command benchmark inference/evaluation, model/API registries, dataset loaders, answer-extraction/judging utilities, video benchmark presets, and helper scripts for data/result workflows.

## Start here

1. **Install or inspect the package.** Use [installation and environment](references/installation-and-environment.md) for install modes, cache roots, optional dependencies, credentials, and format-related environment variables. Run [scripts/check_vlmeval_install.py](scripts/check_vlmeval_install.py) as a safe local diagnostic when a Python environment is available.
2. **Choose the workflow route.** Use the sub-skill map below instead of reading all references.
3. **Keep verification boundaries explicit.** Live API calls need credentials, local VLM runs need model weights/hardware, and dataset builds may download large files. Do not claim those succeeded unless the current task actually runs them.
4. **Troubleshoot cross-cutting failures first.** For install/import, missing `.env`, dependency, cache, output-format, or backend failures, read [troubleshooting](references/troubleshooting.md) before narrowing to a sub-skill.

## Sub-skill routes

- [evaluation](sub-skills/evaluation/SKILL.md): run or resume evaluations, build `run.py`/`torchrun`/`vlmutil` commands, use async API mode, configure judges, scan failed API outputs, summarize `status.json`, and interpret prediction/evaluation artifacts.
- [model-development](sub-skills/model-development/SKILL.md): configure existing VLM/API names, use JSON configs, use OpenAI-compatible/LMDeploy/LiteLLM providers, implement model/API wrappers, register `supported_VLM` entries, and add prompt adapters.
- [benchmark-authoring](sub-skills/benchmark-authoring/SKILL.md): create or adapt benchmark TSV/video data, implement dataset classes, define `build_prompt` and `evaluate`, register image/text/video datasets, add video presets, and write converters.

## Common entry points

| Task signal | Best route | First check |
| --- | --- | --- |
| "Run MMBench/MME/Video-MME on a model" | [evaluation](sub-skills/evaluation/SKILL.md) | Decide `python run.py` vs `torchrun`; pick `--data`, `--model`, `--work-dir`, `--mode`, `--reuse` |
| "Evaluate an OpenAI-compatible endpoint" | [evaluation](sub-skills/evaluation/SKILL.md) then [model-development](sub-skills/model-development/SKILL.md) if adapter/config fails | `--base-url`, `--key`, `--custom-prompt`, `--api-mode`, provider media support |
| "Add a new VLM or API provider" | [model-development](sub-skills/model-development/SKILL.md) | `BaseModel`/`BaseAPI` contract and `supported_VLM` registration |
| "Add a benchmark or custom TSV" | [benchmark-authoring](sub-skills/benchmark-authoring/SKILL.md) | Data columns, `build_prompt`, `evaluate`, `build_dataset`, `--data-config` |
| "Why are results missing or failed?" | [evaluation](sub-skills/evaluation/SKILL.md) | `status.json`, prediction file, checkpoints, failure markers, reuse settings |
| "Package won't import or dependencies conflict" | [troubleshooting](references/troubleshooting.md) | Python version, broad requirements, optional backend deps, `.env` behavior |

## Minimal public import checks

Use these only as diagnostics, not as proof that GPU/API/data workflows are ready:

```bash
python - <<'PY'
import vlmeval
print("vlmeval version:", getattr(vlmeval, "__version__", "unknown"))
from vlmeval.api.litellm_api import LiteLLMAPI
from vlmeval.inference_api import APIEvalPipeline, DatasetConfig
print(LiteLLMAPI.__name__, APIEvalPipeline.__name__, DatasetConfig.__name__)
PY

vlmutil dlist l1
vlmutil mlist all | head
```

A missing `.env` log during import is expected when API keys are not stored in a repository-local `.env`; it is not by itself an import failure.

## Output and verification boundary

This generated skill is self-contained operating guidance. It distills source evidence from VLMEvalKit docs, package code, tests, and safe helper scripts. It includes bundled scripts for install checks, safer torchrun command review, failure scanning, run-summary extraction, and a LongDocURL-style TSV converter. It does not bundle the full evaluation runner, model weights, datasets, API credentials, or service deployments.

Read [repo provenance](references/repo-provenance.md) when checking whether this skill is stale relative to a newer VLMEvalKit checkout. Router metadata for managed import lives in [repo routing metadata](references/repo-routing-metadata.json).
