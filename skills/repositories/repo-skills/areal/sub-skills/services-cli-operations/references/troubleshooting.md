# Services And CLI Troubleshooting

Start with non-invasive inspection: validate command text, inspect config/state files, then use live `status`, `ps`, and `logs` only after the user has approved touching a running service.

## Quick triage flow

1. **Command shape**: run `python scripts/check_service_cli.py --command '...'` to catch missing flags, unsafe defaults, invalid backend specs, and quoting mistakes.
2. **State root**: confirm `AREAL_HOME`. If unset, the CLI uses `~/.areal`.
3. **Service identity**: pass `--service` explicitly when multiple services exist or when current-service may be stale.
4. **Health**: use `areal inf status --json` or `areal agent status --json` to see gateway/router/proxy/worker health.
5. **Logs**: inspect gateway first, then router, then data-proxy/worker logs for the model or pair involved.
6. **Boundary decision**: if failure is agent class contract/import behavior, route to the custom workflow sub-skill; if it is backend worker launch, GPU placement, weight sync, CUDA/NCCL, or model-server memory, route to the distributed backend sub-skill.

## CLI and parser errors

| Symptom | Likely cause | Fix |
|---|---|---|
| `areal: command not found` | AReaL is not installed in the active environment or console scripts are not on `PATH`. | Activate the intended Python environment or run `python -m areal.v2.cli.main --help` to verify importability. |
| `No such command 'new_session'`, `chat`, or `reward` under `areal agent` | The agent CLI intentionally has no session-management subcommands. | Use agent gateway HTTP endpoints for turns and inference gateway HTTP endpoints for sessions/rewards. |
| `--agent is required` | `areal agent run` has no agent import path. | Provide `--agent my_project.agents.MyAgent`. If the class must be written or fixed, route to the custom workflow sub-skill. |
| `--driver must be in 'module.path:func' form` | `areal train run --driver` lacks `:`. | Use `--driver my_project.train:main`. |
| Driver import error or missing function | Python environment cannot import the driver module or function. | Check package installation and module path before running training. |
| `model registration flags require --model` | `areal inf run` received `--backend`/model flags but no `--model`. | Either omit registration flags from `run` and call `areal inf register` later, or include `--model <name>`. |
| `--backend <spec> is required` or `--backend requires --model-path` | Model registration is incomplete. | Provide both `--backend sglang:d1` or `vllm:d...` and `--model-path /path/to/model`. |
| Invalid backend spec | Backend string grammar or engine name is wrong. | Use `sglang:d1`, `sglang:d2t4`, `vllm:d1`, or `vllm:d2t4`. The local CLI only accepts `sglang` and `vllm`. |
| `pp > 1 is not supported by areal inf` | Pipeline parallelism requested in local inference CLI. | Use pipeline size 1 for `areal inf`, or plan a distributed backend setup separately. |

## Quoting and argument splitting

`--engine-args` and `--proxy-args` are shell-style strings split with `shlex.split`. Quote the whole nested argument string.

Bad: outer Click sees nested flags as top-level options.

```bash
areal inf register --model-name qwen --backend sglang:d1 --model-path /models/qwen \
  --engine-args --mem-fraction-static 0.85
```

Good:

```bash
areal inf register --model-name qwen --backend sglang:d1 --model-path /models/qwen \
  --engine-args '--mem-fraction-static 0.85'
```

Run:

```bash
python scripts/check_service_cli.py \
  --command 'areal inf register --model-name qwen --backend sglang:d1 --model-path /models/qwen --engine-args "--mem-fraction-static 0.85"'
```

## State, stale services, and logs

| Symptom | Likely cause | Fix |
|---|---|---|
| `service 'x' is not running` but processes exist | Wrong `AREAL_HOME`, wrong `--service`, or state was removed. | Confirm `AREAL_HOME`, inspect `areal <group> ps --all --json`, and pass `--service` explicitly. |
| `service 'x' gateway is not alive` | State file exists but gateway PID is dead. | Use `areal <group> ps --all`; inspect logs; if intentionally restarting, use `areal <group> run --force ...`. |
| `run` refuses because service already running | Current service slot has a live gateway. | Stop it first with `areal inf stop --service x` or `areal agent stop --service x`; use `--force` only for stale/corrupt state. |
| Logs command says no log named component | Component name does not match a `*.log` stem. | List available components from the error or directory; common names are `gateway`, `router`, `worker-0`, `proxy-0`, `<model>-worker-0`, and `<model>-data-proxy-0`. |
| `status --json` reports some components down | Gateway can read state but health probes fail. | Inspect that component log. Router/data-proxy failures may be service lifecycle; worker failures usually route to backend or agent-class troubleshooting. |

State layout reminder:

- Inference service state: `$AREAL_HOME/inf/services/<service>.json` and `$AREAL_HOME/inf/models/<service>.json`.
- Agent service state: `$AREAL_HOME/agent/services/<service>.json`.
- Logs: `$AREAL_HOME/<namespace>/logs/<service>/*.log`.
- Current pointer: `$AREAL_HOME/<namespace>/current-service`.

`run --force` removes the state slot after trying to kill known PIDs. It is a recovery tool, not normal shutdown.

## Ports, hosts, and admin keys

| Symptom | Likely cause | Fix |
|---|---|---|
| Service fails immediately on startup when binding beyond local host | Built-in demo admin key with a non-local bind may be rejected by key validation. | Use a real secret and bind intentionally: `--host 127.0.0.1` for local-only or provide an operator-approved host and key. |
| Gateway `/health` works locally but remote client fails | Bound to `127.0.0.1`, firewall, container network, or wrong advertised host. | Confirm bind host/port, firewall, and the URL printed by status/logs. |
| `Address already in use` | Port conflict from another service or stale process. | Choose a new port, stop the old service, or use `--force` only after verifying stale state. |
| 401 or 403 from service endpoints | Missing, malformed, or wrong key type. | Check the key taxonomy: admin keys start sessions/manage services; session keys call chat/reward; provider keys are only for external upstreams. |

## Inference session and reward errors

| Symptom | Meaning | Action |
|---|---|---|
| `/rl/start_session` returns 401/403 | Missing or wrong inference admin key. | Use `Authorization: Bearer $INF_ADMIN_KEY`, not the session key or agent key. |
| `/rl/start_session` returns 409 | Requested `api_key` is already bound to an active unfinished session. | End/export the existing session, or start a new session without reusing that key. |
| Client expects `api_key` but response has `sessions[0].session_api_key` | Older helper script or docs assumption. | Update parsing to current response: `group_id` plus `sessions` list. |
| `/chat/completions` succeeds but reward says `No interactions in session` | The chat request was not authenticated with the session key, was routed as standalone, or used a different key. | Ensure `Authorization: Bearer $SESSION_API_KEY` is on the chat request and reward request. |
| `/rl/set_reward` returns 400 with no reward/interaction error | Reward was set before any recorded interaction, or the chosen `interaction_id` is invalid. | Chat first; omit `interaction_id` to reward the latest interaction. |
| `/export_trajectories` returns 400 | `session_ids` missing or empty. | Send `{"session_ids":["..."], ...}` and use the inference admin key. |
| `/export_trajectories` returns 401/404-like router error | Session not registered or already revoked/removed. | Confirm session ID and whether `remove_session=true` or group revocation already ran. |
| 429 capacity/no capacity | Router/worker capacity or staleness control. | Back off and retry. Do not restart services unless health/logs indicate failure. |
| 502 backend worker unreachable | Data proxy or model worker is down/unreachable. | Inspect status/logs. Backend launch, GPU, memory, or model-server errors route to distributed backend troubleshooting. |

## Agent service session and self-evolution errors

| Symptom | Meaning | Action |
|---|---|---|
| `/v1/chat/completions` returns 400 requiring `X-AReaL-Session-Key` or `user` | Chat bridge refuses implicit random route affinity. | Provide `X-AReaL-Session-Key: <stable-key>` or a non-empty `user` field. |
| Agent turns route to different workers | Session key changed between requests. | Reuse the `X-AReaL-Session-Key` response header on subsequent calls. |
| Self-evolution turn returns 400 requiring both fields | `inf_base_url` or `session_api_key` was present without the other. | Send both fields together on the first self-evolution turn. Optional `inf_model` alone does not opt in. |
| Agent receives no `areal_inference` metadata | Self-evolution fields were absent or sent to the wrong endpoint/body level. | Place `inf_base_url`, `session_api_key`, and optional `inf_model` at the top level of the `/v1/responses` or `/v1/chat/completions` request body. |
| Agent worker returns 500 with protocol/type error | Agent class import or `AgentRunnable.run` contract failed. | Route to the custom workflow sub-skill with the error and the agent import path. |
| Structured `/v1/responses` stream is not token-by-token | The bridge re-encodes collected structured output as SSE after the turn completes. | Use raw passthrough `/v1/chat/completions` if byte-for-byte upstream streaming is required and the agent supports `StreamResponse`. |

## Training service errors

| Symptom | Likely cause | Fix |
|---|---|---|
| Training gateway forwards to 401/403 | Wrong training/admin token while routing through gateway/router. | Use the training service admin key for service control; do not substitute inference session keys. |
| Worker says `Engine not created. Call /create_engine first.` | Direct worker endpoint used before controller initialized a training engine. | Use the AReaL controller/trainer path or initialize the worker through the controller. |
| `/offload` or `/onload` fails unexpectedly | Gateway rewrites upstream auth to the admin key, but worker/backend may reject or be unhealthy. | Inspect training gateway and worker logs; backend memory errors route to distributed backend troubleshooting. |
| `areal train run` imports driver then training hangs/fails | Driver started a real training job; failure may be config, backend, scheduler, or model. | Use experiment/backends skills depending on the error class. This service sub-skill only validates invocation shape. |

## Weight update errors

| Symptom | Meaning | Action |
|---|---|---|
| `/connect` in disk mode rejects `save_path` | Disk mode requires an absolute path. | Provide an absolute shared path accessible to train and inference workers. |
| `/connect` rejects LoRA in `awex` mode | Direct AWEX transfer does not support LoRA naming/layout. | Use disk mode and set `use_lora=true` plus `lora_name`. |
| `/update_weights` times out | Train/inference workers, NCCL/HCCL group, or transfer plan stuck. | Collect weight-update gateway logs and worker logs; route to distributed backend troubleshooting. |
| Pair already registered or missing | Duplicate `/connect` or stale `/disconnect` lifecycle. | Disconnect the old pair or use a unique `pair_name`. |

## What evidence to collect before routing away

For backend/GPU/weight-sync issues:

```bash
areal inf status --service <service> --json
areal inf logs --service <service> --component gateway --lines 200
areal inf logs --service <service> --component router --lines 200
areal inf logs --service <service> --component <model>-worker-0 --lines 200
areal inf logs --service <service> --component <model>-data-proxy-0 --lines 200
```

For agent-class issues:

```bash
areal agent status --service <service> --json
areal agent logs --service <service> --component gateway --lines 200
areal agent logs --service <service> --component worker-0 --lines 200
```

For command/config issues, include:

```bash
python scripts/check_service_cli.py --command '<command text>' --json
python scripts/check_service_cli.py --config <toml-file> --config-type inf --json
```
