---
name: aim
description: "Use Aim for experiment tracking SDK instrumentation, local/remote
  run storage, CLI/UI/server workflows, storage maintenance, and ML framework
  logging integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Aim repo skill

Use this skill when a task involves Aim experiment tracking: Python SDK instrumentation, local Aim repositories, run/metric/media/artifact logging, query expressions, Aim CLI/UI/server operation, remote tracking, storage/run maintenance, watcher notifications, or ML framework callback integrations.

## First checks

1. Install the base public package when Aim is not already available:
   ```bash
   python -m pip install aim
   ```
2. Confirm the package and entry points:
   ```bash
   python -c "import aim; print(getattr(aim, '__version__', 'unknown'))"
   aim version
   ```
3. For a reusable diagnostic, run:
   ```bash
   python scripts/check_aim_environment.py --check-optional
   ```
3. Prefer explicit repository paths in both CLI and SDK workflows. Avoid relying on whatever current directory the agent or job scheduler happens to use.

## Route by task

- **Python instrumentation, SDK APIs, metrics/media/params/artifacts, local repo lifecycle, query language, or missing tracked data**: read `sub-skills/tracking-sdk/SKILL.md`.
- **CLI commands, local UI, remote tracking server, notebook UI, run/storage maintenance, conversion command discovery, or watcher/notifier operation**: read `sub-skills/cli-and-services/SKILL.md`.
- **PyTorch/Lightning/Hugging Face/Keras/XGBoost/CatBoost/LightGBM/Optuna/other framework callbacks, optional dependency errors, direct `Run.track` fallbacks, or TensorBoard migration/sync**: read `sub-skills/framework-integrations/SKILL.md`.

## Root references

- `references/package-overview.md` explains Aim's repo/run/sequence/context model and common end-to-end flow.
- `references/troubleshooting.md` covers package-level install/import, version, repository path, cleanup, optional dependency, service, and storage-risk issues.
- `references/repo-provenance.md` records the source commit, package versions, evidence paths, and refresh baseline.
- `references/repo-routing-metadata.json` is structured router metadata for managed repo-skill import tooling.

## Root script

- `scripts/check_aim_environment.py` checks Aim import/version/signatures, safe CLI help/version commands, and optional dependency availability without installing packages, starting services, or mutating repositories.

## Operating guardrails

- Do not run `aim up`, `aim server`, or `aim-watcher start` unless the user asked for a long-running service and gave host/port/lifetime expectations.
- Do not run destructive or storage-mutating commands (`aim runs rm`, `aim storage restore`, `aim storage prune`, `aim storage reindex`, or similar) without listing targets, checking backup/restore context, and getting explicit confirmation.
- Do not install broad ML framework stacks for examples by default. Install or validate only the specific optional dependency required by the user's chosen integration.
- Close Aim `Run` and `Repo` resources explicitly in scripts, especially before deleting temporary repositories.
- Keep generated guidance self-contained. If a workflow needs executable help, use the bundled scripts in this skill tree rather than original repository examples or tests.

## Minimal SDK pattern

```python
from aim import Repo, Run

repo = Repo.from_path("./aim-repo", init=True)
run = Run(repo=repo, experiment="demo", system_tracking_interval=None, capture_terminal_logs=False)
try:
    run["hparams"] = {"lr": 1e-3, "batch_size": 32}
    run.track(0.5, name="loss", step=0, epoch=0, context={"subset": "train"})
finally:
    run.close()
    repo.close()
```

## Minimal CLI pattern

```bash
aim init --repo ./aim-repo
aim up --repo ./aim-repo --host 127.0.0.1 --port 43800
```

For remote training, route to `cli-and-services`: usually start `aim server` on the storage host and point SDK clients at an `aim://...` URL.
