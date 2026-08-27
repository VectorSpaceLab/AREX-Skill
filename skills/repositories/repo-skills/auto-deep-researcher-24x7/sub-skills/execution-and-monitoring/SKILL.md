---
name: execution-and-monitoring
description: "Select and operate local, SSH, or Slurm experiment execution with bounded, zero-LLM monitoring, safe paths, truthful terminal outcomes, and actionable recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Execution and monitoring

Use this skill when an experiment must be launched, inspected, or recovered and
backend choice or liveness semantics matter. It covers the execution boundary,
not the research loop or provider/tool-selection policy.

## Route first

1. Read the `execution.mode` value and the monitor settings.
2. Select exactly one backend: `local`, `ssh`, or `slurm`.
3. Validate required fields before launching anything. For `ssh` and `slurm`,
   controller state remains local while the tool-visible workspace and logs are
   remote. A Slurm login node is a submit/file-operation host, not a place to
   keep a watcher, `tmux`, `srun --wait`, or another persistent job process.
4. Pass command arguments as an argument vector at the backend boundary. Never
   turn untrusted command text into a shell string. Treat `slurm_setup` and
   extra scheduler directives as trusted operator configuration.
5. Record the returned `pid` and `log_file`; for Slurm, `pid` is the integer
   Slurm job id. Then use the zero-LLM monitor until a terminal decision.

See [backends.md](references/backends.md) for constructors, factory fields,
transport, path rules, and scheduler state mapping. See
[monitoring.md](references/monitoring.md) for the polling contract and result
shape. See [troubleshooting.md](references/troubleshooting.md) before retrying.

## Configuration gate

The execution block uses these fields:

- `mode`: `local` (default), `ssh`, or `slurm`.
- `ssh_host`, `remote_workspace`, `remote_python` (default `python3`), and
  `ssh_args` (default `[]`) for remote modes.
- Slurm additionally requires `slurm_partition` and `slurm_time`; it accepts
  `slurm_gpus_per_job`, `slurm_gres`, `slurm_qos`, `slurm_account`,
  `slurm_setup`, `slurm_extra_sbatch`, `slurm_unknown_grace_polls`, and
  `slurm_time_buffer`.
- `monitor.poll_interval` defaults to 900 seconds, `monitor.zero_llm` defaults
  to true, and `monitor.notify_on_complete` defaults to true.

Run the bundled read-only validator when changing these values:

```text
python scripts/check_backend_config.py --config config.yaml
```

It does not connect, submit, launch, or write. Add `--workspace-root DIR
--path RELATIVE_PATH` to check a path against a workspace, including symlink
escape detection.

## Safe launch and monitor contract

The launch tool parses command text with shell-like quoting into `argv`, rejects
an empty command and a small set of destructive executable names, and delegates
with `shell=False`. Semicolons and pipes therefore remain ordinary argument
text; they do not create a second command. A log path is normalized and checked
before the backend creates its parent or opens it.

The monitor performs only backend PID/job liveness, a short log tail, and GPU
status while the job is alive. It makes no LLM call. On completion it reads up
to 50 log lines, extracts common `loss`, `accuracy`, `FGD`, `FID`, `epoch`, and
`step` values, and asks `final_status()` for the backend's terminal evidence.
`status` is `failed` only when `success` is explicitly false; otherwise it is
`completed` with `success` possibly unknown. Treat `success: null` as
indeterminate, not proof of successful training.

For Slurm, never reap a job while `sacct` reports `PENDING` or any running-bucket
state, even after `slurm_time + slurm_time_buffer`: queue time is not bounded by
`--time`. Only unconfirmed probes are bounded by consecutive unknown grace and
the wall-clock backstop. A confirmed Slurm `FAILED`, `TIMEOUT`, `CANCELLED`,
`OUT_OF_MEMORY`, or other failure state must remain failed and be carried into
state/ledger/reporting. A confirmed `COMPLETED` is the only Slurm success.

## Recovery checklist

- `local`: inspect the final log tail and rerun only after deciding whether the
  process ended normally; PID-only final status is inherently indeterminate.
- `ssh`: first verify host/workspace/helper reachability; retry transient SSH
  actions without changing the remote command. Do not create a remote watcher.
- `slurm`: distinguish `PENDING` from unknown. Query `sacct` first; use its
  state as truth, and expect the monitor's bounded unknown handling only when
  accounting/transport cannot confirm the job. A job reaped by the backstop has
  unknown terminal state; reconcile the scheduler and log before calling it a
  success or resubmitting.
- Any path error mentioning “escapes workspace” is a safety stop. Correct the
  relative path; do not weaken normalization or follow a symlink.
