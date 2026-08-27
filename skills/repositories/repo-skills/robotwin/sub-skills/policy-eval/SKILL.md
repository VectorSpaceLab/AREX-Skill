---
name: policy-eval
description: "Configure RoboTwin XPolicyLab policy evaluation, remote policy
  servers, scheduler dry-runs, and action-adapter checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# RoboTwin policy evaluation

Use this sub-skill when the user asks to evaluate a policy in RoboTwin, configure XPolicyLab local or remote evaluation, debug scheduler configs, validate policy action formats, or interpret evaluation result layouts.

## Route first

- For simulation/task-class/render setup, read [simulation-core](../simulation-core/SKILL.md).
- For trajectory datasets used to train/evaluate policies, read [data-pipeline](../data-pipeline/SKILL.md).
- For adding new tasks or language templates, read [task-authoring](../task-authoring/SKILL.md).

## Prerequisites

- A RoboTwin workspace with assets installed and simulation dependencies working.
- If you only have the generated skill tree, use the root [workspace bootstrapper](../../references/workspace-bootstrap.md) first to materialize a pinned public workspace.
- The `XPolicyLab` submodule initialized and a policy adapter under `XPolicyLab/policy/<policy_name>/`.
- Separate policy and evaluation environments when the policy stack and RoboTwin simulation dependencies differ.
- GPU IDs and capacity chosen for the host.

## Main workflows

- **Single/local evaluation and multitask scheduling:** read [evaluation-cli.md](references/evaluation-cli.md). Use `--dry-run` first.
- **Remote policy server + local simulator deployment:** read [remote-server.md](references/remote-server.md).
- **Observation/action adapter semantics:** read [adapter-contract.md](references/adapter-contract.md) and run [scripts/check_action_adapter.py](scripts/check_action_adapter.py) for synthetic qpos/endpose shape checks.
- **Config rendering without launching jobs:** use [scripts/render_eval_config.py](scripts/render_eval_config.py) to inspect a scheduler YAML's effective task list and GPU slots.
- **Failure diagnosis:** read [troubleshooting.md](references/troubleshooting.md).

## Evaluation modes

1. `bash scripts/eval_policy.sh serve --config env_cfg/eval/remote_server.yml` starts a pool of policy servers.
2. `bash scripts/eval_policy.sh multitask --config env_cfg/eval/all_tasks.yml ...` schedules local policy+simulator jobs or local simulator clients against remote servers.
3. Without `multitask` or `serve`, `scripts/eval_policy.sh` dispatches a single eval call to the XPolicyLab adapter path.

## Validation signals

- `--dry-run` prints the schedule and concrete commands without launching policies.
- Scheduler config rejects unknown fields, duplicate tasks, invalid GPU IDs, missing checkpoint in local mode, and missing remote endpoints in remote mode.
- `eval_result/multitask/<run_id>/summary.json` reports jobs total/succeeded/failed/skipped.
- Per-task logs are under `eval_result/multitask/<run_id>/logs/`.
- Single task eval writes `_result.txt` under `eval_result/<task>/<policy>/<task_config>/<checkpoint>/<timestamp>/`.
