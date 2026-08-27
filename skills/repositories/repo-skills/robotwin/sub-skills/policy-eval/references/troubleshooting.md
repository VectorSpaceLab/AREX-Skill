# RoboTwin policy evaluation troubleshooting

## `XPolicyLab is not initialized`

Symptom: scheduler validation says `XPolicyLab/setup_policy_server.py` is missing.

Recovery:

```bash
git submodule update --init --recursive XPolicyLab
```

If using the updater script, understand it fetches upstream and mutates the submodule pin. Do not run update/stage/install modes without user intent.

## Missing policy adapter script

Symptoms mention missing:

- `XPolicyLab/policy/<policy_name>/eval.sh`
- `XPolicyLab/policy/<policy_name>/setup_eval_env_client.sh`
- `XPolicyLab/policy/<policy_name>/setup_eval_policy_server.sh`

Recovery:

1. Confirm the policy name exactly matches an adapter directory.
2. Confirm the submodule branch/pin includes that policy.
3. Use the adapter's documented environment and checkpoint format.

## Scheduler config errors

Common failures:

- `tasks must be a non-empty list`.
- Duplicate task names.
- Unknown scheduler YAML fields.
- Invalid GPU range or duplicate GPU IDs.
- `--policy-conda-env is required when enable_remote is false`.
- `--ckpt-name is required when enable_remote is false`.
- Remote endpoint flags used without `--enable-remote`.

Recovery: run `--dry-run`, simplify to one task, and render the config with `render_eval_config.py` before launching.

## Action response errors

Symptoms:

- `Policy returned an empty action chunk`.
- `Missing left/right arm joint action`.
- `left ee action must have dim 7`.
- Rollouts step but never succeed.

Recovery:

1. Match `--action-type` to policy output: `joint`/`qpos` for joint vectors, `ee`/`endpose` for 7D end-effector poses.
2. Use adapter key names from [adapter-contract.md](adapter-contract.md).
3. Run `check_action_adapter.py --repo-root <workspace> --env-cfg-type arx_x5 --action-type joint` (or `--action-type ee`) and pass an action JSON/file when checking a concrete payload.
4. Confirm policy reset/prepare-case methods are implemented or safely ignored by the adapter.

## Expert check skips too many seeds

Expert check runs the task expert path before policy rollout. It can skip seeds that are unstable, planning-failed, or erroring.

Recovery:

- Start with `--test-num 1` and clean task config.
- Confirm assets and render smoke through [simulation-core](../../simulation-core/SKILL.md).
- Temporarily use `--no-expert-check` only if the user understands that evaluation seeds may include impossible/unstable episodes.
- Increase `--max-seed-attempts` for batch evaluation if many seeds are unstable.

## Remote server is not ready

Likely causes:

- Port already in use.
- `bind_host` not reachable from client host.
- Policy environment failed to start.
- Checkpoint path is wrong on the policy host.

Recovery:

1. Run server mode with `--dry-run` to inspect commands.
2. Use a unique `base_port` range.
3. Check server logs under the configured `output_dir`.
4. For remote clients, set `--policy-server-ip` to a connectable host, not `0.0.0.0`.

## Result files missing or incomplete

- Multitask summary missing: scheduler crashed before summary write or output directory was not writable.
- Per-task `_result.txt` missing: single rollout crashed before completion.
- Job failed in summary: inspect `logs/<job_id>.log` and the command recorded at top of the log.
