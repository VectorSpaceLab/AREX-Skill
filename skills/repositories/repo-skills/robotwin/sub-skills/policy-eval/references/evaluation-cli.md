# RoboTwin evaluation CLI

## Dispatcher behavior

`eval_policy.sh` is the public ready-workspace dispatcher, and the generated skill also bundles `scripts/robotwin_workspace.py eval` as a self-contained dispatcher wrapper for users who start from the skill tree.

- First argument `serve` runs the policy-server pool launcher.
- First argument `multitask`, or any command containing `--config`, runs the multitask scheduler.
- Otherwise it runs the single evaluation adapter.

Always start with a dry run for scheduler/server modes.

## Local multitask evaluation

Self-contained generated-skill pattern. Run this from the generated skill root (`skills/disco/robotwin/`) or replace `scripts/robotwin_workspace.py` with its absolute path:

```bash
python scripts/robotwin_workspace.py eval \
  --workspace /path/to/robotwin-workspace -- \
  multitask \
  --config env_cfg/eval/all_tasks.yml \
  --policy-name <policy_name> \
  --ckpt-name <checkpoint> \
  --env-cfg-type arx_x5 \
  --policy-conda-env <policy_env> \
  --eval-env-conda-env <robotwin_env> \
  --action-type joint \
  --dry-run
```

Ready-workspace native pattern:

```bash
bash scripts/eval_policy.sh multitask \
  --config env_cfg/eval/all_tasks.yml \
  --policy-name <policy_name> \
  --ckpt-name <checkpoint> \
  --env-cfg-type arx_x5 \
  --policy-conda-env <policy_env> \
  --eval-env-conda-env <robotwin_env> \
  --action-type joint \
  --dry-run
```

Remove `--dry-run` only after the printed commands are correct.

Important CLI flags:

| Flag | Meaning |
| --- | --- |
| `--config` | scheduler YAML; required |
| `--policy-name` | XPolicyLab policy adapter directory name |
| `--ckpt-name` | checkpoint path/name; required for local mode |
| `--env-cfg-type` | XPolicyLab robot/action profile, e.g. `arx_x5` |
| `--policy-conda-env` | environment used by policy adapter local server |
| `--eval-env-conda-env` | environment used by RoboTwin simulator client |
| `--bench-name` | default `RoboTwin` |
| `--action-type` | `joint` or `ee`/`endpose` family |
| `--seed` | base evaluation seed |
| `--jobs-per-gpu` | override config capacity |
| `--task-config` | default `demo_clean` |
| `--test-num` | episodes per task |
| `--eval-batch`, `--num-workers` | batch evaluation mode for batch-safe/stateless policies |
| `--instruction-type` | override `seen`/`unseen` |
| `--expert-check` / `--no-expert-check` | whether expert path filters seeds |
| `--frequency` | observation/action frequency passed to policy adapter |
| `--output-dir` | default `eval_result/multitask` |
| `--fail-fast` | stop scheduling after first failure |
| `--stream-output` | stream raw logs instead of progress display |

## Scheduler config fields

The scheduler YAML accepts only:

- `gpu_ids`: list, comma-separated IDs, or range like `0-7`.
- `jobs_per_gpu`: positive integer.
- `num_workers`: per-task batch workers.
- `tasks`: non-empty list of task names.
- `enable_remote`: boolean.
- `policy_server_ip`, `policy_server_port`: remote endpoint(s).

Unknown fields are rejected, which is useful for catching typos early.

## Local vs remote validation

Local mode requires `--policy-conda-env` and `--ckpt-name`. Remote mode forbids policy-server flags unless `--enable-remote` is active and requires connectable server host/port values.

## Output layout

Multitask scheduler output:

```text
eval_result/multitask/<run_id>/
  summary.json
  logs/<job_id>.log
  jobs/<job_id>.args
```

The summary includes run duration, GPU capacity, remote endpoints, jobs finished/succeeded/failed/skipped, and per-job commands/status.

## Safe preflight checklist

1. Initialize `XPolicyLab` and confirm `XPolicyLab/setup_policy_server.py` exists.
2. Confirm `XPolicyLab/policy/<policy_name>/eval.sh` exists for local mode.
3. Confirm `env_cfg/<env_cfg_type>.yml` exists and XPolicyLab defines the same action profile.
4. Trim `tasks` to one or two tasks for the first dry run.
5. Use `--test-num 1` for the first real smoke.
6. Keep `render_freq: 0` in the task config unless you need videos.
