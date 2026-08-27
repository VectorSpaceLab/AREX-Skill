---
name: environment-maintenance
description: "Guides OpenLLM installation checks, cache and per-Bento
  virtual-environment maintenance, GPU resource compatibility, cleanup safety,
  and analytics opt-out."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Environment Maintenance

Use this sub-skill for OpenLLM operational diagnostics that are not about one specific model command.

## Typical triggers

- Install/import checks, `openllm --version`, or `pip check`
- `OPENLLM_HOME`, repository cache, temp directory, or per-Bento venv questions
- `openllm clean ...`
- NVIDIA/NVML GPU detection or insufficient resources
- `BENTOML_DO_NOT_TRACK`
- Cache corruption or model-specific dependency installation failures

## What this route covers

- OpenLLM's home/cache/config layout.
- Per-Bento virtual environment creation and cleanup behavior.
- Resource compatibility scoring for local and cloud targets.
- Safe cleanup command handling.
- Hardware probe and import diagnostics.

## Read next

- [references/environment-reference.md](references/environment-reference.md) for OpenLLM home, config, cache, and per-Bento venv details.
- [references/resource-compatibility.md](references/resource-compatibility.md) for `Resource`, `DeploymentTarget`, GPU map, and `can_run` behavior.
- [references/troubleshooting.md](references/troubleshooting.md) for install, cache, cleanup, and hardware failures.
- [scripts/check_installation.py](scripts/check_installation.py) for a safe runtime diagnostic.
- [scripts/estimate_bento_resources.py](scripts/estimate_bento_resources.py) for a safe resource-spec parser and target comparison.

## Boundaries

Do not start models from this route. Use `local-serving` for live servers and `cloud-deployment` for live deploys. Use `model-repositories` for repo URL/model catalog issues.
