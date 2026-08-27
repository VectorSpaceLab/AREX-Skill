# Troubleshooting and safe recovery

Use this matrix before changing project code or starting another experiment. The
first response is read-only unless the row explicitly names a human-controlled
steering file.

| Symptom | Likely cause | Safe diagnosis | Recovery |
|---|---|---|---|
| Validator says `PROJECT_BRIEF.md` is missing/empty | Wrong project root or incomplete project | Confirm `--project` and list only the project root | Create a concise human-owned brief; do not let a worker invent the goal. |
| Validator says config cannot be parsed | YAML syntax or unsupported fallback syntax | Re-run with `--json`; inspect the named config text only | Fix YAML and re-run validator. Do not start the loop with an unparsed config. |
| Validator rejects `mandatory_dry_run: false` | Unsafe run contract | Confirm the effective value in the checker output | Set it to true. Require a fresh tiny dry-run before launch. |
| Loop starts but no experiment launches | Leader chose `wait`, provider returned a wait fallback, or worker did not call the launch tool | Read `state.status`, `suggested_next_step`, and `autoresearcher.log` | If intentional, allow cooldown. If unexpected, fix the provider/worker handoff in its routed skill; do not manually launch a duplicate. |
| Worker reports training in prose but no PID/log is in state | Structured launch result missing or provider bypassed the worker protocol | Compare the worker response with `state.json` and tool result fields | Treat the launch as unverified. Do not monitor or report success from prose; route provider/tool protocol diagnosis. |
| Dry-run was not reported | Worker skipped the mandatory invariant or result was incomplete | Inspect worker handoff and training log timestamps | Stop before real training; request a small dry-run and an explicit pass/fail report. |
| `status: running` is old | Child may be alive, crashed, or state update stopped | Compare `updated_at` and query the selected backend; then inspect log tail | If alive, do not relaunch. If terminal, preserve the terminal evidence and reflect. If absent, restart with `--max-cycles 1` and a clear directive. |
| Same plan repeats without metrics | No progress or failed execution is being retried | Inspect normalized task/hypothesis, `last_error`, and recent ledger lines if enabled | Let fallback produce `wait`, or place a specific directive to pivot/retest. Never increase the cycle cap as the first response. |
| Fallback did not trigger | A directive is present, action is not `experiment`, threshold is disabled, or plan signature changed | Check `last_directive`, action, threshold, and task/hypothesis text | This can be correct. Remove/consume an intentional directive and make the next plan materially different only when justified. |
| Directive was not consumed | File is empty, wrong workspace, or controller has not reached cycle start | Check effective `project.workspace`, file size, and `state.status` | Write a non-empty file in the configured workspace and wait for the next cycle. Do not use undocumented `--directive`. |
| Directive archive file already exists | Two directives consumed in one second or a prior archive collision | List `directive_archive` and preserve existing files | Rename the new file to a unique name only with human approval, then restart conservatively. Never overwrite an existing directive. |
| Leader chose `report` but loop continued | The output schema advertises `report`, but only `wait` has a special branch | Inspect the next `state.status`, worker result, and reflection | Treat `report` as intent, not a stop primitive. Stop the controller after validating the handoff, or steer the next cycle explicitly. |
| `--directive` is rejected by argparse | Stale documentation/example | Run `python -m core.loop --project PROJECT --help` | Use `workspace/HUMAN_DIRECTIVE.md`; do not patch the running installation during an experiment. |
| `--check` is rejected without a project | `--project` is required even for check mode | Run `python -m core.loop --project PROJECT --check` | Use the bundled checker for project validation and `--check` for the installation/status printout. |
| `max_cycles` appears ignored | Persisted `.cycle_counter` already meets the cap, or CLI override was not used | Compare `.cycle_counter`, `state.cycle`, and the command line | Use a deliberately higher finite cap only after inspecting evidence; do not delete the counter. |
| Controller restart repeats old context | Expected cycle-local leader history is reset; persistent project memory remains | Compare brief, memory log, cycle number, and directive archive | Keep the brief/memory; re-run bounded and provide a directive if the next decision needs context. |
| Local PID commands fail for a Slurm job | `execution.mode: slurm` stores a scheduler job id, not a local PID | Check mode and scheduler fields; query scheduler status through backend workflow | Use `sacct`/backend semantics. If local behavior is required, switch mode explicitly and revalidate. |
| Slurm config launches with `--gpu 0` but GPU is not pinned | Expected: scheduler allocates GPUs and the CLI GPU value is ignored | Read `execution.mode`, `slurm_gres`, and `slurm_gpus_per_job` | Configure the scheduler request; do not treat `--gpu` as an allocation override. |
| Terminal result says failure with empty metrics | Real training or scheduler failure, not a successful launch | Preserve `terminal_state`, log tail, and `last_error` | Reflect the failure, fix the cause, and only retry with a changed hypothesis or explicit directive. |
| State is malformed JSON | Interrupted/non-atomic write or manual edit | Copy/inspect the file without modifying it; check logs and counter | Preserve the damaged evidence, stop the controller, and use the memory/progress skill's state-repair procedure. Do not have this skill silently rewrite it. |

## Safe stop checklist

1. Record the controller PID from the process supervisor, not from
   `state.json.pid` unless the backend is known to be local and the field came
   from a launch result.
2. Send SIGINT/SIGTERM to the controller only.
3. Re-read `state.json` and the training log.
4. Verify child terminal/liveness through the selected backend.
5. Cancel a still-running child using the backend-specific procedure.
6. Restart with `--max-cycles 1`, preserve the cycle counter, and provide a
   directive explaining whether to resume, pivot, or report.

## Safe result triage

Classify the result in this order:

1. **Launch verified?** Require a structured PID/job id and log path.
2. **Dry-run passed?** Missing evidence means not verified.
3. **Terminal truth?** Preserve the backend's `status` and `terminal_state`.
4. **Metrics present?** Empty metrics are absence, not zero.
5. **Goal comparison?** Compare to the brief and prior trusted baseline.
6. **Next action?** Continue, pivot, wait, or report with the reason recorded.

This ordering prevents a stale PID, a provider's prose, or an optimistic milestone
from being mistaken for a reproducible scientific result.
