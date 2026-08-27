# State and Experiment Troubleshooting

## Research Wiki Is Empty

Run the read-only helper resolver first. If the helper exists, initialize at the Git project root, not an arbitrary subdirectory. Check that `query_pack.md`, `log.md`, and graph edges were created. If the project has a manual copy instead of `.aris/tools`, keep the copy consistent with the installed ARIS release.

## Session Was Compacted or Interrupted

Read status and contract files before asking the model to continue. Inspect `REVIEW_STATE.json` and traces for review loops. If no durable checkpoint exists, report the missing evidence and avoid claiming the stage completed.

## Watchdog Says a Job Is Dead

Confirm session type (`screen` vs `tmux`), exact session name, and whether the job intentionally exited. Check status JSON and alerts. Do not restart automatically if the job may have produced partial results; inspect logs and checkpoints first.

## GPU Utilization Is Empty

`nvidia-smi` may be missing, the process may be CPU-bound, or the task may run on a remote host. Use session/file progress and explicit remote checks instead. Empty utilization is not a pass or fail by itself.

## Remote Experiment Cannot Be Recovered

Check SSH reachability, project path, environment activation, and the screen/tmux session independently. Preserve queue state and experiment logs. Do not create a second job until the first host's state is known.

## Results and Claims Drift

Route raw results through the result-to-claim/audit stages. A better-looking metric does not automatically support a broader claim; record scope, baseline, seed, and evaluation protocol.
