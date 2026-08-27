# Backend reference

## Common interface

All three backends implement the same execution interface:

- `validate()` checks the workspace or remote prerequisites.
- `read_file(path) -> str` and `read_file_range(path, start_line=1, end_line=None) -> str`.
- `write_file(path, content) -> dict`.
- `list_files(path=".") -> list[str]`, `list_tree(path=".", max_depth=3, max_entries=300) -> list[str]`, and `grep_files(pattern, path=".", max_results=50, ignore_case=False) -> list[dict]`.
- `run_command(argv, timeout=120, env=None) -> dict`.
- `launch_command(argv, log_file, env=None) -> dict`.
- `is_process_alive(pid) -> bool`, `tail_file(path, lines=50) -> list[str]`, and `get_gpu_status() -> dict`.
- `final_status(pid) -> {"state": str, "success": bool|None}`. The base implementation is `{"state": "unknown", "success": None}`.

The launch result includes `pid`, `log_file`, and a status. `ExperimentMonitor`
uses the PID key for all backends. In Slurm, that PID-shaped value is the job
id, not an operating-system process id.

## Factory and exact constructors

The factory is conceptually:

```python
build_execution_backend(config: dict | None, controller_workspace: Path)
```

It reads `config.get("execution", {})` and defaults to `mode="local"`.
Unknown modes raise `ValueError` and list `local, ssh, slurm`.

```python
LocalExecutionBackend(workspace: Path)
SSHExecutionBackend(
    ssh_host: str,
    remote_workspace: str,
    remote_python: str = "python3",
    ssh_args: list[str] | None = None,
)
SlurmExecutionBackend(
    ssh_host: str,
    remote_workspace: str,
    remote_python: str = "python3",
    ssh_args: list[str] | None = None,
    slurm_partition: str = "",
    slurm_time: str = "",
    slurm_gpus_per_job: int | None = None,
    slurm_gres: str = "",
    slurm_qos: str = "",
    slurm_account: str = "",
    slurm_setup: str = "",
    slurm_extra_sbatch: list[str] | None = None,
    slurm_unknown_grace_polls: int = 4,
    slurm_time_buffer: int = 1800,
)
```

The factory passes each matching YAML field through, converts Slurm grace and
buffer values to integers, and uses `[]` for omitted list fields. It does not
silently fall back from a requested remote mode to local mode.

## Local

`LocalExecutionBackend` resolves its workspace at construction. `validate()`
creates that workspace if needed. File operations, commands, process launches,
log reads, and `nvidia-smi` queries run on the controller machine with the
workspace as current directory. `run_command` returns the last 2,000 stdout
characters and last 500 stderr characters; a timeout returns an `error` field.
`launch_command` opens a normalized log path, redirects stdout and stderr to the
same file, starts a new session, and returns the OS PID. A local PID check can
say whether a process exists, but after it exits the backend cannot recover its
exit code; final success is therefore unknown.

## SSH

`SSHExecutionBackend.validate()` requires `ssh_host`, `remote_workspace`, and a
local `ssh` executable, then invokes a remote `validate` action. The remote
workspace is expanded/resolved by the helper and created by validation. Every
ordinary operation sends one JSON payload over stdin to a transient SSH command;
the helper returns one JSON object and exits. The encoded helper is an
implementation detail, not an interactive shell session and not a process to
keep alive.

The remote action contract is: `read_file`, `read_file_range`, `write_file`,
`list_files`, `list_tree`, `grep_files`, `run_command`, `launch_command`,
`is_process_alive`, `tail_file`, `get_gpu_status`, and `validate`. Remote errors
are mapped to `FileNotFoundError`, `NotADirectoryError`, or `ValueError` where
recognized; other failures are `RuntimeError`. Invalid JSON, nonzero SSH exit,
and transport timeout are actionable `RuntimeError`s.

`run_command` sends an argv list and environment separately. SSH itself is
invoked without a local shell. The only shell-string helper, `_ssh_shell`, is
reserved for scheduler probes/cancellation in the Slurm subclass; interpolated
job ids are converted to integers and operator configuration is the remaining
trusted input. There is no persistent login process.

## Slurm

`SlurmExecutionBackend` subclasses SSH. File/repo operations and ordinary short
commands use the shared remote helper on the login node, assumed to share the
workspace with compute nodes. Only experiment launch, scheduler liveness,
queue status, and cancellation differ.

Before use, `validate()` additionally requires nonempty `slurm_partition` and
`slurm_time`, then checks that `sbatch`, `sacct`, and `squeue` are all present on
the submit host. Missing any one is an actionable configuration error.

### Submit-and-exit launch

`launch_command` normalizes the log path, derives a job name as `ar_` plus the
log path stem, and sends a `submit_slurm` action. The helper safely builds a
small batch script and invokes `sbatch --parsable` with an argv list and no
caller-supplied shell string. It sets `--chdir` to the workspace, quotes the
relative `--output` path, applies `--time`, partition, optional QoS/account,
extra directives, setup, and the command. The log parent is created first.

`slurm_gres` takes precedence over numeric `slurm_gpus_per_job`. The helper
removes `CUDA_VISIBLE_DEVICES` and `GPU` from the job environment so an agent's
local GPU mask cannot pin a scheduler allocation. The returned parsable token
may be `jobid;cluster`; only the numeric job id is retained. Non-numeric or
failed `sbatch` output is an error. No `tmux`, `srun --wait`, polling loop, or
other persistent login-node process is part of submission. `cancel(pid)` is a
best-effort transient `scancel` and returns false on transport failure.

### Scheduler truth

`sacct` is the liveness authority while reachable. The backend queries one job
with `State%30`, removes a trailing `+`, and takes the first token (so
`CANCELLED by <uid>` is handled). If sacct is empty, it makes a transient
`squeue` query for a job too new or absent from accounting. An empty result from
both is `unknown`.

State buckets are exact:

| Bucket | States |
|---|---|
| running | `PENDING`, `RUNNING`, `REQUEUED`, `RESIZING`, `SUSPENDED`, `CONFIGURING`, `COMPLETING` |
| completed | `COMPLETED` only |
| failed | `FAILED`, `TIMEOUT`, `CANCELLED`, `NODE_FAIL`, `OUT_OF_MEMORY`, `BOOT_FAIL`, `DEADLINE`, `REVOKED`, `SPECIAL_EXIT` |
| unknown | empty/unrecognized/transport failure, including `PREEMPTED` |

A confirmed running bucket always returns alive, including a job that has been
queued for longer than `--time`. A confirmed terminal bucket returns not alive
and is cached for `final_status()`: only `COMPLETED` maps to success true;
recognized failure maps to false. If an unknown job is reaped by a safeguard,
no terminal state was observed and final success remains null.

The `--time` parser accepts bare minutes, `minutes:seconds`,
`hours:minutes:seconds`, and day-prefixed variants. Invalid/empty time gets a
large sentinel in the liveness cap, so it does not spuriously reap; validation
still requires a nonempty configured time.
