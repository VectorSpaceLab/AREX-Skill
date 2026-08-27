---
name: fate
description: "Operate FATE 2.2.0 federated-learning deployments, FateFlow
  Pipeline workflows, local launchers, and component CLI/runtime inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# FATE

Use this repository skill when a task involves **FATE / FederatedAI/FATE 2.2.x**: installing or checking the package, starting FateFlow-backed services, writing service-backed `FateFlowPipeline` jobs, running service-free local launchers, or inspecting the local component runtime exposed by `python -m fate.components`.

## Start here

1. Read `references/package-overview.md` for package names, installed surfaces, backend boundaries, and the sub-skill map.
2. Run `scripts/check_fate_install.py` to summarize the active Python environment before giving commands that depend on installed FATE packages.
   - Add `--include-service` when the user needs `fate_flow`, `pipeline`, or FateFlow-backed Pipeline workflows.
   - Add `--strict` only when the task should fail on missing optional/service surfaces.
3. Route to the smallest matching sub-skill below; keep root guidance for package-wide setup, routing, and cross-cutting troubleshooting.
4. If a user reports behavior from a newer or older checkout, compare against `references/repo-provenance.md` before assuming this skill is current.

## Sub-skill routing

| User task | Read this first |
| --- | --- |
| Install FATE, choose PyPI vs Docker/Compose/host deployment, initialize or check FateFlow services, diagnose ports/Docker/SSH/service startup | `sub-skills/deployment/SKILL.md` |
| Upload data, build `FateFlowPipeline` DAGs, use Reader/PSI/preprocessing/train/evaluate/deploy/predict, validate upload YAML | `sub-skills/pipeline-workflows/SKILL.md` |
| Run without FateFlow using `fate.arch.launchers`, multiprocessing parties, dataframe readers, or direct `fate.ml` trainers | `sub-skills/local-launchers/SKILL.md` |
| Inspect component descriptors, component list, hyphenated `task-schema`, artifact types, task config schema, or custom component discovery | `sub-skills/component-runtime/SKILL.md` |

## Root operating boundaries

- The verified baseline is a CPU Python inspection/runtime surface. Do not claim GPU, DeepSpeed, Spark, Eggroll cluster, RabbitMQ, Pulsar, or Docker-cluster execution is verified unless the user provides and you verify that backend.
- Service-backed workflows require a running FateFlow service and initialized `pipeline` client. Local launchers and component CLI inspection do not require FateFlow.
- Treat deployment shell scripts and cluster rollout scripts as reference workflows by default. Do not run destructive service, Docker, SSH, or root OS mutation commands unless the user explicitly requests that action and the target is clear.
- The bundled references and scripts are self-contained for operating guidance. Do not rely on the original repository checkout for runtime instructions.
- When in doubt between Pipeline and local launcher APIs, ask whether the user wants a FateFlow-backed job or a service-free local simulation.

## Repository-wide references

- `references/package-overview.md` — package/import/CLI surfaces, install footprint, backend limits, and capability ownership.
- `references/troubleshooting.md` — cross-cutting install/import, service, CLI, data/config, and backend diagnostics.
- `references/repo-provenance.md` — source commit, package versions, dirty-state note, and relative evidence paths for staleness checks.
- `references/repo-routing-metadata.json` — structured router placement metadata for this repo skill.

## Safe root helper

```bash
python scripts/check_fate_install.py
python scripts/check_fate_install.py --include-service --strict
python scripts/check_fate_install.py --json
```

The helper only imports packages, checks versions, runs help commands, and reports backend/service surfaces. It does not start services, contact FateFlow, upload data, launch training, or mutate the host.
