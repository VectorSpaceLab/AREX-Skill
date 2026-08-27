---
name: wandb
description: "Use W&B's Python SDK and CLI for experiment tracking,
  offline/local workflows, artifacts and registries, Public API exports,
  automations, sweeps, and Launch jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# W&B Repo Skill

Use this skill when a task involves the `wandb` Python package, the `wandb`/`wb` CLI, experiment tracking, local/offline run management, artifacts/model registry, Public API queries, automations, hyperparameter sweeps, or W&B Launch jobs.

## Install and Verify

For ordinary users, install the public package:

```bash
python -m pip install wandb
python - <<'PY'
import wandb
print(wandb.__version__)
print(wandb.init)
PY
```

Use optional extras only when the workflow needs them:

- Cloud artifact storage: `wandb[aws]`, `wandb[gcp]`, or Azure storage/identity packages.
- Rich media logging: `wandb[media]` plus framework/media libraries used by the data.
- Sweeps/Launch/cloud queues: `wandb[sweeps]`, `wandb[launch]`, and provider SDKs or container tooling required by the target backend.
- Workspaces or model helpers: `wandb[workspaces]` or `wandb[models]` when a task explicitly uses those surfaces.

For a local source checkout, expect compiled helper artifacts such as `wandb-core` to be built. If source installation fails, read `references/troubleshooting.md` before broadening dependencies.

Run the bundled environment check when you need a safe local diagnostic:

```bash
python scripts/check_wandb_environment.py --check-cli
```

## Route by Workflow

- **Experiment tracking in Python:** Use `sub-skills/experiment-tracking/SKILL.md` for `wandb.init()`, `Run.log()`, config, summary, tables/media/plots, metric axes, notebooks, offline/disabled modes, and tracking smoke checks.
- **CLI and local/offline workflows:** Use `sub-skills/cli-and-local-workflows/SKILL.md` for `wandb login`, `wandb init`, `wandb status`, `wandb offline/online/disabled`, `wandb sync`, local run directories, environment variables, cache cleanup, Docker wrapping, and self-hosted host configuration.
- **Artifacts and registries:** Use `sub-skills/artifacts-and-registries/SKILL.md` for `wandb.Artifact`, `Run.log_artifact()`, `Run.use_artifact()`, artifact aliases/versions, downloads, `wandb artifact ...`, storage references, registry linking, and model registry troubleshooting.
- **Public API and automations:** Use `sub-skills/public-api-and-automation/SKILL.md` for `wandb.Api`, querying runs/projects/sweeps/files/reports/artifacts, exporting history, pagination, and automation events/filters/actions/scopes.
- **Sweeps and Launch:** Use `sub-skills/sweeps-and-launch/SKILL.md` for sweep YAML/JSON, `wandb.sweep()`, `wandb.agent()`, `wandb sweep`, `wandb agent`, Launch jobs, queues, launch agents, resource backends, and structural config validation.

## Shared References

- `references/repo-provenance.md`: read before deciding whether this skill is current for a different W&B checkout or before running a refresh.
- `references/troubleshooting.md`: use for cross-cutting install/import, authentication, base URL, optional dependency, source-build, and local service issues.
- `scripts/check_wandb_environment.py`: safe diagnostics for installed package version, importability, CLI availability, optional extras, and selected environment variables with secrets redacted.

## Safe Defaults

- Prefer `with wandb.init(...) as run:` so runs finish even when code raises.
- Use `mode="offline"` for credentials-free testing and local-only capture; sync later with CLI guidance.
- Never print API keys or `.netrc` contents. Treat `WANDB_API_KEY` as present/absent only.
- Use full W&B paths such as `entity/project/run_id` or `entity/project/artifact:alias` when defaults could resolve to the wrong account.
- For destructive commands such as `wandb sync --clean` or cache cleanup, explain what will be deleted and ask before running them.
- Do not invent cloud credentials, queues, Kubernetes contexts, container registries, IAM roles, bucket names, or self-hosted server URLs.

## Common Cross-Workflow Paths

- If a training script needs both tracking and datasets/models, start with `experiment-tracking`, then route artifact inputs/outputs to `artifacts-and-registries`.
- If an offline run must be uploaded later, instrument with `experiment-tracking` and use `cli-and-local-workflows` for `wandb sync`.
- If a report/export task references existing runs, use `public-api-and-automation`; if it needs to create future runs, route back to `experiment-tracking`.
- If a sweep trial logs metrics or artifacts, use `sweeps-and-launch` for orchestration, `experiment-tracking` for trial logging, and `artifacts-and-registries` for data/model lineage.

## Freshness Check

This skill was generated from repository evidence and live package inspection. Read `references/repo-provenance.md` if the current checkout, package version, public CLI/API, tests, or docs have changed. If the provenance differs materially, refresh the skill from the repository before relying on exact signatures or command behavior.
