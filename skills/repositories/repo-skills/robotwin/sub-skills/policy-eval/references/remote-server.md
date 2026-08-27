# Remote policy server deployment

Remote mode splits policy inference and local RoboTwin simulation:

1. Start one or more XPolicyLab policy servers on the policy host.
2. Run the RoboTwin simulator scheduler locally with `--enable-remote` and server endpoints.

## Server config

Server YAML fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `policy_name` | yes | XPolicyLab policy adapter name |
| `checkpoint` | yes | checkpoint path/name on the policy host |
| `env_cfg_type` | yes | action/robot profile name |
| `action_type` | yes | `joint` or `ee`/`endpose` family |
| `policy_env` | yes | policy host environment name |
| `gpu_ids` | yes | list/string/range of GPUs |
| `instances_per_gpu` | yes | server processes per GPU |
| `base_port` | no | first server port; default 18080 |
| `bind_host` | no | host to bind; default `0.0.0.0` in code, template may use `127.0.0.1` |
| `bench_name` | no | default `RoboTwin` |
| `server_task_name` | no | use actual task name for task-bound policies |
| `seed` | no | policy seed |
| `startup_timeout` | no | readiness wait seconds |
| `output_dir` | no | policy server log root |

The server launcher rejects placeholder values like `<policy_name>` and unknown fields.

## Start servers

Pattern on the policy-server host:

```bash
bash scripts/eval_policy.sh serve --config env_cfg/eval/remote_server.yml --dry-run
bash scripts/eval_policy.sh serve --config env_cfg/eval/remote_server.yml
```

The launcher builds one command per GPU/instance and waits for WebSocket readiness by probing each port.

## Run local simulator clients

Pattern on the simulator host:

```bash
bash scripts/eval_policy.sh multitask \
  --config env_cfg/eval/all_tasks.yml \
  --policy-name <policy_name> \
  --env-cfg-type arx_x5 \
  --eval-env-conda-env <robotwin_env> \
  --enable-remote \
  --policy-server-ip <server_ip> \
  --policy-server-port <port> \
  --dry-run
```

`--policy-server-ip` and `--policy-server-port` can be repeated. A single IP may pair with multiple ports, or IP and port lists can have matching lengths.

## Readiness and shutdown

- The server launcher treats `0.0.0.0` bind host as `127.0.0.1` for local readiness probes.
- It performs a WebSocket upgrade probe and sends a close frame.
- Keyboard interrupt terminates launched server process groups and closes logs.
- Real server logs live under the configured server `output_dir`.

## Common remote-mode decisions

- Use `bind_host: 127.0.0.1` for same-host testing; use a routable interface only when remote clients need network access.
- Use a unique port range for each server pool.
- Keep task lists small until server throughput and simulator throughput are understood.
- If the policy is stateful or not batch-safe, avoid `--eval-batch` or more than one simulator client per policy server.
