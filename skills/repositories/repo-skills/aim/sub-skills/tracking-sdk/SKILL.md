---
name: tracking-sdk
description: "Use Aim's Python SDK to create local repositories and runs, track
  metrics/params/media/artifacts/logs, query sequences, and validate SDK
  instrumentation safely."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo-skill: aim
  scope: sub-skill
license: Apache 2.0
---

# Aim tracking SDK

Use this sub-skill when the task is to instrument Python code with Aim, open or initialize a local Aim repository from Python, create/resume/read runs, track scalar/object sequences, attach run metadata, query tracked data, build dataframes, or diagnose SDK-level missing-data issues.

Route away from this sub-skill when the user asks for:

- CLI command syntax, UI/server startup, remote server operation, storage maintenance, or destructive run management: use `cli-and-services`.
- Framework callbacks/loggers, optional ML framework integrations, or TensorBoard conversion/sync: use `framework-integrations`.

## What to read

- `references/sdk-api-reference.md` for `Run`, `Repo`, `Sequence`, `SequenceCollection`, object constructors, artifacts, logging, lifecycle, and known signature caveats.
- `references/tracking-workflows.md` for copyable SDK instrumentation patterns, including train/validation loops with params and media.
- `references/query-and-data-model.md` for query expressions, contexts, sequence iteration, dataframes, and query edge cases.
- `references/troubleshooting.md` for missing metrics, type compatibility, temporary-directory cleanup, read-only misuse, system tracking, and validation steps.
- `scripts/aim_sdk_smoke.py` to create a tiny local repo, track scalars/media, query results, exercise dataframe paths when available, and verify the read-only caveat safely.

## Operating guardrails

1. Prefer explicit repository paths in automation: create or open `Repo.from_path(str(repo_dir), init=True)` and pass the `Repo` object to `Run(repo=repo, ...)`.
2. Close `Run` objects and then close `Repo` objects explicitly before deleting temporary directories or ending validation processes.
3. Disable background/system capture for short tests unless the user specifically needs it: `Run(system_tracking_interval=None, log_system_params=False, capture_terminal_logs=False)`.
4. Use `Run(run_hash, repo=repo, read_only=True)` or `repo.get_run(run_hash)` for read access. In the verified Aim version, `Repo(..., read_only=True)` raises `NotImplementedError`.
5. Keep each sequence homogeneous for a fixed `(run, name, context)` tuple. Use distinct contexts such as `{"subset": "train"}` and `{"subset": "val"}` when logging the same metric name for different phases.
6. Use `QueryReportMode.DISABLED` in scripts and tests to avoid progress-bar side effects.
7. Do not start long-running UI/server processes or run destructive storage commands from this sub-skill.

## Minimal pattern

```python
from aim import Repo, Run

repo = Repo.from_path("./aim-repo", init=True)
run = Run(repo=repo, experiment="demo", system_tracking_interval=None, capture_terminal_logs=False)
try:
    run["hparams"] = {"lr": 1e-3, "batch_size": 32}
    for step in range(3):
        run.track(1.0 / (step + 1), name="loss", step=step, epoch=0, context={"subset": "train"})
        run.track(0.8 / (step + 1), name="loss", step=step, epoch=0, context={"subset": "val"})
finally:
    run.close()
    repo.close()
```
