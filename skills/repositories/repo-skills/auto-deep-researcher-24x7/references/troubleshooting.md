# Cross-cutting troubleshooting

Use the narrow sub-skill troubleshooting file first. This matrix covers
failures that cross installation, configuration, resources, and reporting.

| Symptom | Likely cause | Safe next action |
|---|---|---|
| `ModuleNotFoundError: yaml`, `anthropic`, or `openai` | Runtime requirements are not installed in the Python that launches the application | Install the documented requirements into the intended project environment; rerun the read-only `--check` and import smoke. Do not repair an unrelated environment silently. |
| `python -m core.loop --check` fails before status output | Wrong working/import path or missing `core` modules | Run from the application installation context or make the application package available; inspect Python identity and import paths. `--check` does not prove provider/GPU/remote readiness. |
| `PROJECT_BRIEF.md` missing/empty | Project contract is incomplete | Create a human-owned brief with goal, metric/target, code/data, constraints, and stop rules. Do not generate a substitute brief from model guesses. |
| Validator reports `mandatory_dry_run` false | Unsafe lifecycle configuration | Set `experiment.mandatory_dry_run: true`; require the code worker to perform a tiny dry-run before launch. |
| `execution.mode` invalid or remote fields missing | YAML typo or incomplete SSH/Slurm configuration | Run the backend validator; select exactly `local`, `ssh`, or `slurm` and fill only the fields required by that mode. |
| `Path escapes workspace` or symlink escape error | Absolute/parent path or symlink would leave the workspace | Correct the relative path and preserve the safety check. Do not use a shell or weaken normalization. |
| Provider unknown, no key, or CLI missing | Unsupported label, unset credential environment, or uninstalled/logged-out CLI | Run provider metadata validation, confirm only the environment-variable name, then install/login or choose an available provider. Never print or persist a secret. |
| Worker summary has no authoritative PID/log | Provider bypassed text tool protocol or launch did not return structured JSON | Use `anthropic`, `openai`, or `claude_cli` for workers; treat `codex_cli` worker prose as non-authoritative and inspect the backend before retrying. |
| Training appears `completed` but local/SSH result is uncertain | PID-only backends cannot recover exit codes after process exit | Inspect the final log and experiment artifact directly; report terminal success as unknown unless evidence proves it. |
| Slurm job remains `PENDING` | Queue wait is legitimate | Do not reap it based on `--time`; query `sacct`/`squeue` and leave it alive while a running bucket is confirmed. |
| Slurm state is unknown repeatedly | Accounting/SSH gap or purged job | Let bounded unknown grace/backstop terminate waiting; preserve `success: null`, reconcile scheduler/log evidence, and do not claim success. |
| `sbatch`, `sacct`, or `squeue` missing | Submit host is not a prepared Slurm login node | Stop before launch; configure a real submit host or use local/SSH mode. |
| No GPUs or CUDA unavailable | Driver, visibility, wheel, or resource problem | Run the read-only GPU probe, then a minimal framework CUDA check. Route to CPU only when the selected workflow has a truthful CPU substitute; otherwise treat GPU capability as blocked. |
| Repeated `waiting`/fallback | Same plan produced no progress | Inspect ledger/journals/log; use a non-empty human directive for deliberate steering or change the hypothesis. Do not delete history to reset the signal. |
| State says `running` but no process/log update | Stale state, remote filesystem issue, or dead child | Verify with the selected backend, inspect `updated_at`, scheduler state, and log path. Stop/reconcile before relaunching. |
| Malformed ledger lines | Partial write or manual edit | Preserve original bytes; readers skip invalid lines. Append valid future records and report malformed-line counts. |
| Journal rotation fails or archive collision appears | Filesystem permission/space or same-second archive name | Preserve the live file, inspect `.bak` archives and disk/permissions, and stop for human review if history may collide. |
| Obsidian export says disabled or writes to an unexpected place | `obsidian.enabled` false, empty vault path, or configured fallback | Confirm the target before enabling; empty `vault_path` means project-local fallback. Treat dashboard/daily writes as explicit side effects. |
| Installer refuses a Codex destination | Destination lacks the repository ownership marker | Do not overwrite. Review the destination manually or use a disposable fixture; marker-gated uninstall is the safe boundary. |
| Source and generated skill roots are mixed | Existing `skills/` contains source skills and a generated `disco/` root | Keep the generated graph under its own active root; do not merge it into source skills or run a live import as part of this graph construction. |

If evidence conflicts, preserve the conflict and unresolved limit in the report.
Do not turn a skipped credential, network, hardware, scheduler, or expensive
check into a pass.
