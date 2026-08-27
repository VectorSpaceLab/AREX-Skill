# Troubleshooting analysis and publication workflows

Diagnose from the first structured error and the relevant local/remote record.
Do not retry a paid execution, remote mutation, or destructive command until the
failure class and target are known.

| Symptom | Likely cause | Safe next step |
|---|---|---|
| `analyze` says path is neither trial nor job | Missing `trial.log`/`job.log`, wrong nesting, or a task path was supplied | Point to the trial or job directory; use `check` for task quality and `run-evaluate` for execution. |
| Analysis/check exits with an evaluator error | Missing model key, agent/extra, provider, Docker, or malformed rubric | Run `--help`, validate rubric syntax and `harbor --version`; classify provider/credential failure before retrying. |
| `--passing` and `--failing` are rejected together | Mutually exclusive filters | Choose one; inspect rewards directly when the primary reward key is absent. |
| Analysis output is missing or incomplete | Derived analysis job failed, source trial was malformed, or a prior analysis artifact was excluded | Read the derived job's `result.json`, each trial `result.json`, and `analysis.json`; never edit the source result to repair it. |
| Viewer cannot detect folder type | No child job has `config.json`, or no child task has `task.toml` | Pass `--jobs`/`--tasks` explicitly and point at a parent containing subdirectories. |
| Viewer reports no port or browser cannot connect | Port range occupied, bind address inaccessible, or static assets unavailable | Use a free loopback port; keep `--host 127.0.0.1`; use packaged assets or `--no-build`; do not run a frontend build during an audit. |
| Viewer appears to change data | Local viewer reads the supplied folder; a build/dev run changed frontend assets instead | Stop the server, compare the data tree, and treat `--build`/`--dev` as side-effecting. |
| Hub returns not found/empty | Invalid UUID, record is private/not shared, wrong scope, or network/auth failure | Validate UUID and login; try `--scope shared|all` only when authorized; use `--json` and preserve the raw response. |
| Hub list is hard to script | Interactive pager or terminal formatting | Pipe/non-TTY mode, `--json`, `--quiet`, `--page`, `--no-headers`, and a fixed `--columns` selection. |
| Retry affects unexpected trials | Filters selected latest attempts or a broad job scope | Preview `hub job trials` with identical filters and `--include-retries` as needed; retry requires owner approval and confirmation. |
| Regrade refuses the source | No result/manifest, missing artifact bytes, failed/skipped manifest entry, multi-step source, or shared-mode replacement verifier | Repair/collect valid source evidence or author a separate-mode single-step verifier; do not rerun the agent or overwrite the source. |
| Regrade score changes unexpectedly | Verifier changed, task input mapping differs, artifact is stale, or reward keys differ | Compare source/regrade config, lock, manifest, verifier logs, and reward dictionaries; use the printed delta and retain both directories. |
| Job/trial download says unauthenticated | No Harbor login or expired session | Stop; ask the user to authenticate with the supported Harbor auth flow. Do not request or print a token. |
| Download refuses existing directory | Destination collision and no overwrite | Select a new parent or explicitly approve `--overwrite`; inspect any existing result first. |
| Download reconstructs a job with missing trials | Full archive unavailable or one trial archive is inaccessible | Read `download_manifest.json` and warnings; do not call the partial reconstruction complete. |
| Upload rejects a local job | Missing job `config.json`/`result.json`, malformed trial, expired auth, or permission/visibility issue | Validate the local tree, check auth/owner/org, then rerun the idempotent upload only after approval. |
| Upload partially succeeds | Trial archive failure or transient storage/network error | Keep the job; record uploaded/failed trial IDs and rerun the same upload to fill missing trials. |
| Re-upload changes visibility unexpectedly | Explicit `--public`/`--private` was passed | On existing jobs omit visibility to preserve it; verify server state with Hub reads before any update. |
| Publish says no task/dataset found | Path is wrong, has neither manifest, or contains no immediate task children | Run local task/dataset checks and pass the exact directory; use `--no-tasks` only when the task package graph is already published. |
| Publish digest/version differs | Local tasks or metric changed, `sync` was not run, or package was resolved by a mutable tag | Review the manifest diff, sync intentionally, and pin a revision/digest for reproducibility. |
| Tag move is refused | Tag points at another revision, target is yanked, or tag syntax is invalid | Inspect with `version list/show`; use `--force` only after explicit approval and never tag a yanked version. |
| Trace export finds no trials | Wrong root, non-recursive search, missing `agent/trajectory.json`, or unsupported ATIF agent | Point at a trial/job root, enable recursion, inspect agent files, and record unsupported/malformed omissions. |
| Trace export rejects multimodal content | Images are referenced but exporter cannot represent them in the selected format | Preserve the original ATIF; export a compatible subset or use an alternate format only after confirming data loss. |
| Trace push/OTLP upload fails | Missing repo/endpoint, token/header, network, or remote permission | Validate local export first; check the exact destination and credentials, then retry only the failed external operation. |
| Parity row has blank sides/std/runs | One-sided/malformed metric or alternate key not recognized | Preserve raw JSON, flag the row, and extend the reporting schema deliberately rather than inventing values. |

## Minimal evidence bundle for escalation

Collect the Harbor version, exact command with secrets removed, local path/UUID,
exit code, first error, relevant `config.json`/`lock.json` fields, result and
manifest status, and whether the operation was local, credentialed, networked,
Docker, GPU, or Windows. Include only the smallest artifact/log excerpts needed
to explain the failure. Mark optional capability failures as unverified rather
than as core Harbor failures.
