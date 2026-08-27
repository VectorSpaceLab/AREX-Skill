---
name: cli-and-services
description: "Operate Aim CLI, local UI, remote tracking services, notebook UI,
  conversion discovery, storage maintenance, and watcher notifications safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Aim CLI and services sub-skill

Use this sub-skill when the task is about Aim's command-line entry points, UI/server operation, remote tracking endpoints, notebook UI, run/storage maintenance, conversion command discovery, or watcher/notifier setup.

Route away from this sub-skill when the user asks for:

- Python SDK instrumentation, `Run.track`, media objects, query expressions, or run metadata modeling: use `tracking-sdk`.
- Framework callbacks/loggers or detailed TensorBoard conversion workflows: use `framework-integrations`.

## Operating rules

1. Prefer explicit repository paths. Pass `--repo <repo_dir>` to CLI commands instead of relying on the current working directory.
2. Classify commands before running them:
   - Safe by default: `aim --help`, `aim version`, `aim <command> --help`, `aim-watcher --help`, `aim init --repo <empty_or_existing_dir> --skip-if-exists`.
   - Long-running: `aim up`, `aim server`, `aim-watcher start`. Do not start these unless the user asked for a listener/service and provided host/port/process-lifetime expectations.
   - Destructive or mutating maintenance: `aim runs rm`, `aim runs mv`, `aim runs close`, `aim runs update-metrics`, `aim storage upgrade 3.11+`, `aim storage restore`, `aim storage prune`, `aim storage reindex`. List/backup/confirm first.
3. For reverse proxies, distinguish the UI (`aim up`) from the remote tracking API (`aim server`). They are different services and usually need different ports or process managers.
4. Never paste Slack webhooks, Workplace access tokens, SSL keys, or other credentials into logs, generated code, or shared reports.
5. Use the bundled smoke script for safe command availability checks; it intentionally does not start listeners or run destructive maintenance.

## References

- `references/cli-reference.md` — entry points, commands, verified flags, and safe command patterns.
- `references/services-and-remote-tracking.md` — choosing `aim up` vs `aim server`, client `aim://` URLs, SSL, base paths, notebook UI, Docker concept, and deployment cautions.
- `references/storage-and-run-maintenance.md` — list-first maintenance workflows for stale/corrupted runs and storage/index operations.
- `references/troubleshooting.md` — common command, repository, service, remote, notebook, and notifier failures.

## Script

Run the safe smoke check from any directory:

```bash
python scripts/aim_cli_smoke.py --help
python scripts/aim_cli_smoke.py
python scripts/aim_cli_smoke.py --init-dir ./aim-smoke-repo
```

The script checks `aim`/`aim-watcher` help and version commands, creates only a temporary or user-selected initialized repo with `--skip-if-exists`, and skips service listeners and destructive maintenance.
