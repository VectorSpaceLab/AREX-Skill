# Execution and monitoring troubleshooting

Use the smallest recovery that preserves the safety boundary. Do not “fix” a
transport problem by switching to local execution unless the operator explicitly
accepts that the code, data, and logs are on the controller.

| Symptom | Likely meaning | Safe response |
|---|---|---|
| `Unknown execution.mode` | Typo or unsupported backend | Use exactly `local`, `ssh`, or `slurm`; re-run the read-only validator. |
| `ssh_host ... required` / `remote_workspace ... required` | Remote fields are incomplete | Fill both fields; do not silently fall back to local. |
| `ssh binary not found on PATH` | Controller lacks the SSH client | Install/provision SSH outside this skill, then run validation again. |
| SSH action timeout/nonzero exit/invalid JSON | Host, remote Python, auth, or remote helper problem | Check host access, remote interpreter, and workspace reachability with a short operator check; retry transiently. Never start a watcher on the host. |
| `Path escapes workspace` | Absolute path, `..`, or a resolving symlink leaves the root | Stop. Use a relative path under the configured root and remove/repair the symlink. Never bypass the resolver. |
| `Path cannot be empty` / file-not-found | Missing or malformed relative path | Supply the intended workspace-relative path; for missing logs, verify the launch result and shared filesystem. |
| `Blocked executable` | Command parser rejected a destructive executable | Do not disguise it with shell syntax or a path alias. Use an explicitly reviewed, narrow operation if appropriate. |
| Shell metacharacters appear in output but no side effect | Expected `shell=False` behavior | Quote the intended argv and use a dedicated executable; pipes/redirections are not interpreted. |
| `sbatch/sacct/squeue` not found | Submit host is not a usable Slurm login node | Correct `ssh_host` or provision scheduler tools; do not emulate Slurm with a background login process. |
| `sbatch failed` or no numeric job id | Invalid partition/time/directive/command or scheduler refusal | Read the returned error and scheduler reason, fix configuration, then submit a new job only after checking whether a job was actually created. |
| Log parent missing on Slurm | A job output directory was not available | The helper normally creates the parent before submit. Verify the normalized log path and shared workspace; do not use an outside path. |
| Job is `PENDING` for a long time | Queue wait, not a dead job | Keep it alive. `--time` limits running wall time, not queue wait; inspect queue reason with the operator's scheduler tools. |
| `sacct` is empty but `squeue` says pending/running | Job is new or not yet in accounting | The fallback state is authoritative for the current probe; do not reap it. |
| `sacct`/SSH is temporarily unreachable | Indeterminate liveness | Let bounded unknown grace absorb a short outage. Restore access and query the same job id before resubmitting. |
| Unknown probes exceed grace | Liveness cannot be confirmed | The monitor is intentionally bounded and may stop waiting. Reconcile with `sacct`, `squeue`, and the log before declaring failure or success. |
| Unknown job passes `--time + buffer` | Wall-clock anti-hang backstop | Waiting ends with terminal state unknown. Treat outcome as unresolved; do not report success without scheduler/log evidence. |
| Slurm reports `FAILED`, `TIMEOUT`, `CANCELLED`, or `OUT_OF_MEMORY` | Confirmed non-success terminal state | Preserve `status=failed` and the raw terminal state. Diagnose log/resource/config cause before retrying. |
| Local/SSH process disappeared with `success: null` | PID-only backend cannot recover exit code | Inspect final log and project state. Report completed-but-indeterminate, not proven success. |
| GPU status is `N/A` | `nvidia-smi` unavailable, query failed, or SSH is not GPU-capable | Continue only if the experiment can run without that signal; do not claim a GPU allocation. Slurm status is queue occupancy, not device utilization. |
| Monitor appears idle | It is intentionally sleeping between polls | Check `poll_interval`, the tracked PID/job id, and the log. Do not add an LLM polling loop. |
| Tail is empty while job is alive | No output yet, wrong path, buffering, or shared-filesystem lag | Verify the exact returned `log_file`; wait briefly and inspect scheduler state. Do not overwrite or redirect outside the workspace. |

## Difficult-case invariants

### PENDING versus unknown

A confirmed `PENDING`/running-bucket response resets the consecutive unknown
counter and returns alive forever if necessary. The wall-clock cap is consulted
only after the state is indeterminate. This is deliberate: reaping a queued job
because its requested runtime elapsed would create duplicate jobs.

### Symlink and traversal defense

Normalize the user path first: reject blank, absolute, or any `..` component.
Then resolve the candidate with `strict=False` and require it to remain below the
workspace root. This second check catches a benign-looking relative path such
as `link/output.log` when `link` points outside. Walk/list/grep operations also
skip symlink entries rather than following them. Apply the check before opening,
creating a parent, or writing content.

### Safe scheduler commands

Submit commands are argv-quoted into a temporary batch script and submitted
with `sbatch --parsable`; ordinary remote commands use JSON-over-SSH. Scheduler
state probes are one transient SSH invocation at a time. Job ids are parsed and
converted to integers before interpolation. Never copy an arbitrary user
string into an `_ssh_shell` command or replace submit-and-exit with `tmux`,
`nohup` on the login node, or a controller-side scheduler loop.
