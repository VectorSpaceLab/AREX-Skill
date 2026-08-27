---
name: metaflow
description: "Guides Metaflow workflow authoring, local and remote execution,
  client/data access, cards, dependency environments, deployment orchestration,
  and repository maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Metaflow Repo Skill

Use this skill when a task involves the `metaflow` Python package, Metaflow flow scripts, Metaflow client objects, runtime decorators, cards, deployment backends, or maintaining the Metaflow repository. Metaflow is a workflow framework for building, running, observing, scaling, and deploying data science and ML systems from Python `FlowSpec` classes.

## Start Here

1. Install or verify Metaflow in the target environment:
   ```bash
   python -m pip install metaflow
   python - <<'PY'
   import metaflow
   print(metaflow.__version__)
   PY
   ```
2. If automation cannot infer a username, set one before running flow CLIs:
   ```bash
   export USERNAME=${USERNAME:-disco}
   ```
3. For a local flow script, prefer:
   ```bash
   python flow.py --no-pylint check
   python flow.py run --max-workers 1
   python flow.py version
   ```
   The top-level `metaflow` command has no `--version` option; flow scripts expose `version` as a subcommand.
4. For a quick public-package diagnostic, run [`scripts/check_metaflow_environment.py`](scripts/check_metaflow_environment.py).

## Route By Task

| User intent | Read |
| --- | --- |
| Write, check, run, resume, or debug a local `FlowSpec`; use `Parameter`, `Config`, `IncludeFile`, foreach, or local decorators | [`sub-skills/flow-authoring/SKILL.md`](sub-skills/flow-authoring/SKILL.md) |
| Run flows from Python code, notebooks, or subprocess wrappers with `Runner`, `NBRunner`, `Deployer`, or returned `ExecutingRun` objects | [`sub-skills/runner-and-programmatic/SKILL.md`](sub-skills/runner-and-programmatic/SKILL.md) |
| Query runs/artifacts/logs/tags through `Flow`, `Run`, `Task`, metadata, namespaces, datastores, or `S3` datatools | [`sub-skills/client-and-data/SKILL.md`](sub-skills/client-and-data/SKILL.md) |
| Add or inspect Metaflow Cards, `current.card`, card CLI output, task logs, sidecars, or runtime observability | [`sub-skills/cards-and-observability/SKILL.md`](sub-skills/cards-and-observability/SKILL.md) |
| Use AWS Batch, Kubernetes, Argo Workflows, Step Functions, Airflow, projects, schedules, events, secrets, or remote compute resources | [`sub-skills/deployment-orchestration/SKILL.md`](sub-skills/deployment-orchestration/SKILL.md) |
| Configure `@pypi`, `@conda`, `--environment=conda|pypi|uv`, code packaging, package suffixes, or extension/plugin loading | [`sub-skills/dependency-environments/SKILL.md`](sub-skills/dependency-environments/SKILL.md) |
| Modify this repository, choose tests, follow contributor policy, or work with devstack/stubs/R/package maintenance | [`sub-skills/repo-maintenance/SKILL.md`](sub-skills/repo-maintenance/SKILL.md) |

## Shared References

- Read [`references/api-and-cli-overview.md`](references/api-and-cli-overview.md) for verified public imports, high-level CLI groups, and common object names.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import, username, optional dependency, and source-dependency mistakes.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is current for a Metaflow checkout or should be refreshed.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) provides structured routing metadata for managed repo-skill import.

## Boundaries

- Local authoring and package inspection are CPU-capable. Cloud, Kubernetes, Argo, Airflow, Azure, GCP, S3 service, devstack, and GPU/PyTorch parallel paths require the relevant credentials, services, or hardware and are not proven by a CPU import.
- This skill is for using or maintaining Metaflow. For unrelated MLOps packages, choose the package-specific skill instead.
- Runtime guidance is self-contained. Do not require future agents to open the original repository checkout; use the bundled references and scripts here.
