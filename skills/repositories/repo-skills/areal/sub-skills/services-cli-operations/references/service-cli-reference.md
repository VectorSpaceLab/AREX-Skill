# AReaL 2.0 Service CLI Reference

This reference distills the AReaL 2.0 service and CLI contracts into a self-contained operating guide. Command examples are intentionally concrete but use placeholders. They are not executed by the bundled checker.

## Service surfaces at a glance

| Surface | Main entry | Primary components | Use it for | Side-effect level |
|---|---|---|---|---|
| Inference service | `areal inf ...` | Gateway, router, model workers, data proxies | OpenAI-compatible local inference service, model registration, online RL session capture | `run`, `register`, `deregister`, `stop` mutate runtime |
| Agent service | `areal agent ...` | Gateway, router, data-proxy/worker pairs | Serving pluggable agent classes with session affinity and optional self-evolution routing | `run`, `stop` mutate runtime |
| Training driver | `areal train run ...` | User training driver function | Invoke an AReaL training script with config and Hydra-style overrides | Starts training |
| Direct modules | `python -m areal.v2.*` | Individual gateway/router/worker/data-proxy processes | Low-level debugging or controller integration | Starts services |
| Weight update | `python -m areal.v2.weight_update.gateway` plus HTTP API | Weight-update gateway | Connect train/inference workers and push versions | Starts service; HTTP calls mutate weight state |

For backend worker/GPU placement failures, use the distributed backend sub-skill. For writing the agent class itself, use the custom data/rewards/workflows sub-skill.

## Before composing live commands

1. Confirm the AReaL runtime variant is appropriate for the requested backend: SGLang for default inference service, or vLLM variant when registering vLLM workers.
2. Decide an `AREAL_HOME`. If unset, the CLI uses `~/.areal`. For tests or parallel experiments, set a separate value:

   ```bash
   export AREAL_HOME="$HOME/.areal/my-experiment"
   ```

3. Use non-demo admin keys for any service bound beyond local-only development:

   ```bash
   export INF_ADMIN_KEY='replace-with-a-secret'
   export AGENT_ADMIN_KEY='replace-with-a-secret'
   ```

4. Validate command strings before execution:

   ```bash
   python scripts/check_service_cli.py \
     --command 'areal inf register --model-name qwen --backend sglang:d1 --model-path /models/qwen'
   ```

## `areal inf` command matrix

`areal inf` manages a local inference service. It accepts `--config FILE`; values in that extra TOML override `$AREAL_HOME/inf/config.toml`, and explicit CLI flags override both.

| Command | Purpose | Key options | Notes |
|---|---|---|---|
| `areal inf run` | Start gateway and router, optionally register one model at startup | `--service`, `--host`, `--port`, `--admin-api-key`, `--routing-strategy {round_robin,least_busy}`, `--log-level`, `--launch-timeout`, `--detach`, `--force`, optional `--model`, `--backend`, `--model-path`, `--tokenizer-path`, `--engine-args`, `--proxy-args`, `--model-health-timeout`, `--scheduler local` | Starts processes. If `--backend` is provided without `--model`, the CLI rejects it. If `--model` is provided, `--backend` and `--model-path` are required. |
| `areal inf register` | Register a model against a running service | `--model-name`, `--service`, `--backend`, `--model-path`, `--tokenizer-path`, `--engine-args`, `--proxy-args`, `--model-health-timeout`, `--log-level` | Spawns worker and data-proxy replicas, then registers their addresses with router/gateway. |
| `areal inf deregister` | Remove a model and tear down its workers | `--model-name`, `--service`, `--grace`, `--force` | Router unregisters first, then data proxies are killed, then workers. |
| `areal inf models` | List registered models for one service | `--service`, `--json` | Reads model-state. |
| `areal inf status` | Probe gateway/router/proxy/worker health | `--service`, `--json` | Probes component `/health` endpoints and prints placement/GPU/address/ref/alive columns. |
| `areal inf ps` | List known services | `--all`, `--json` | Includes stale services only with `--all`; `ps` has no `--service` flag. |
| `areal inf logs` | Tail a component log | `--service`, `--component gateway`, `--lines`, `--follow` | Uses `tail`; component names include `gateway`, `router`, and generated worker/data-proxy names. |
| `areal inf stop` | Stop one service | `--service`, `--grace`, `--force`, `--keep-state` | Stops data proxies, workers, gateway, then router; `--keep-state` preserves state files. |

### Inference model registration details

Backend specs use the same allocation grammar as AReaL inference configs, but `areal inf` only spawns `sglang` and `vllm` workers locally:

```bash
# One SGLang data-parallel replica, one tensor-parallel rank.
areal inf register \
  --service inf-demo \
  --model-name qwen \
  --backend sglang:d1 \
  --model-path /models/qwen \
  --tokenizer-path /models/qwen \
  --engine-args '--mem-fraction-static 0.85 --max-running-requests 256' \
  --proxy-args '--request-timeout 120 --chat-template-type hf'

# Two data-parallel vLLM replicas, each using tensor parallel size 4.
areal inf register \
  --service inf-demo \
  --model-name qwen-vllm \
  --backend vllm:d2t4 \
  --model-path /models/qwen \
  --engine-args '--gpu-memory-utilization 0.90'
```

Rules:

- `--model-path` is required for internal worker registration.
- `--tokenizer-path` defaults to `--model-path` when omitted.
- `--engine-args` and `--proxy-args` are shell-style strings parsed with `shlex.split`; quote the whole value so nested flags are not mistaken for outer CLI options.
- Pipeline parallelism above `p1` is rejected by the local `areal inf` registration path.
- GPU allocation and worker-start failures are backend problems; route those to the distributed backend sub-skill after collecting logs.

### Start, inspect, and stop example

```bash
areal inf run \
  --service inf-demo \
  --host 127.0.0.1 \
  --port 8080 \
  --admin-api-key "$INF_ADMIN_KEY" \
  --detach

areal inf register \
  --service inf-demo \
  --model-name qwen \
  --backend sglang:d1 \
  --model-path /models/qwen

areal inf status --service inf-demo
areal inf models --service inf-demo --json
areal inf logs --service inf-demo --component gateway --lines 100
areal inf stop --service inf-demo --grace 10
```

## `areal agent` command matrix

`areal agent` manages a service that wraps a pluggable agent class. It accepts `--config FILE`; values in that extra TOML override `$AREAL_HOME/agent/config.toml`, and explicit CLI flags override both.

| Command | Purpose | Key options | Notes |
|---|---|---|---|
| `areal agent run` | Launch gateway, router, and N data-proxy/worker pairs | `--service`, `--agent`, `--num-pairs`, `--admin-api-key`, `--setup-timeout`, `--health-poll-interval`, `--drain-timeout`, `--session-timeout`, `--log-level`, `--force` | `--agent` is required and is a Python import path such as `my_pkg.agents.MathAgent`. |
| `areal agent status` | Show component health | `--service`, `--watch`, `--interval`, `--json` | Probes gateway/router/workers/data proxies. |
| `areal agent ps` | List known agent services | `--all`, `--json` | Includes stale services only with `--all`. |
| `areal agent logs` | Tail component logs | `--service`, `--component gateway`, `--lines`, `--follow` | Uses the same logs contract as `areal inf`. |
| `areal agent stop` | Stop an agent service | `--service`, `--grace-period`, `--keep-state`, `--force` | Kills known component PIDs and optionally removes state. |

The agent CLI intentionally does not expose session-management verbs such as `new_session`, `chat`, or `reward`. Use HTTP endpoints on the agent gateway and the inference gateway session APIs instead.

### Agent service HTTP surfaces

| Endpoint | Auth | Purpose | Key request fields |
|---|---|---|---|
| `GET /health` | none | Gateway health | none |
| `POST /v1/responses` | agent admin key | OpenAI Responses-compatible structured turn | `input`, `instructions`, `model`, `user`, optional `metadata`, optional `stream`, optional self-evolution fields `inf_base_url`, `inf_model`, `session_api_key` |
| `POST /v1/chat/completions` | no agent-admin gate at the gateway; route internally uses service admin key | OpenAI chat-completions-compatible raw passthrough | `messages`, `model`, and either `X-AReaL-Session-Key` header or `user` field for route affinity; optional self-evolution fields |
| `POST /sessions/close` | agent admin key | Close an agent session | `session_key` |
| `WS /ws?token=...` | agent admin token query parameter | WebSocket request/response frame bridge | request frames with method `agent` and a `sessionKey` |

Session affinity rules:

- `/v1/responses`: `X-AReaL-Session-Key` wins when supplied; otherwise a key is derived from `user` and `model` (`agent:<model>:<user>`). Without either, the bridge may mint a unique key for the request.
- `/v1/chat/completions`: `X-AReaL-Session-Key` wins; otherwise `user` derives `chat:<model>:<user>`. If neither is present, the request is rejected with `400` so multi-turn callers are not silently split across workers.
- The resolved key is echoed in the `X-AReaL-Session-Key` response header. Reuse it on later turns.

## `areal train` command matrix

`areal train run` invokes a user training driver. It does not validate that the resulting training job is cheap or that GPUs are available.

```bash
areal train run \
  --config /path/to/experiment.yaml \
  --driver my_project.train:main \
  experiment_name=my-exp trial_name=trial-0 rollout.backend=sglang:d1 actor.backend=fsdp:d1
```

Rules:

- `--config` is required and must point to an experiment YAML.
- `--driver` is required and must be `module.path:function`.
- Extra tokens after `--driver` are passed through to the driver's AReaL config loader as overrides.
- Driver import errors and missing function names are reported before the function is called. Once called, the driver owns all training side effects.

## Config files and precedence

All service-style CLIs use this precedence:

1. Explicit CLI flag.
2. Extra TOML passed by `--config FILE`.
3. Namespace default config at `$AREAL_HOME/<namespace>/config.toml`.
4. Built-in click option default.

### Inference TOML keys

The TOML loader does not expand shell variables. Replace placeholders with literal values before live execution.

```toml
[default]
service = "inf-demo"
admin_api_key = "replace-with-inference-admin-key"
log_level = "info"

[launch]
gateway_host = "127.0.0.1"
gateway_port = 8080
routing_strategy = "round_robin"
launch_timeout = 30.0

[scheduler]
type = "local"

[register.internal]
backend = "sglang:d1"
model_health_timeout = 600.0
engine_args = "--mem-fraction-static 0.85"
proxy_args = "--request-timeout 120 --chat-template-type hf"
```

Binding notes:

- `[default].service` applies to `run`, `stop`, `status`, `register`, `deregister`, `models`, and `logs`.
- `[default].admin_api_key` and `[default].log_level` apply to `run`.
- `[scheduler].type` applies to `run`; current CLI scheduler choice is `local`.
- `[register.internal]` applies to `register`, not to `run` startup registration unless the corresponding CLI flags are provided.

### Agent TOML keys

The TOML loader does not expand shell variables. Replace placeholders with literal values before live execution.

```toml
[default]
service = "agent-demo"
admin_api_key = "replace-with-agent-admin-key"
log_level = "info"

[run]
agent = "my_project.agents.HermesAgent"
num_pairs = 1
setup_timeout = 120.0
health_poll_interval = 5.0
drain_timeout = 30.0
session_timeout = 1800.0
```

Binding notes:

- `[default].service` applies to `run`, `stop`, `status`, `ps`, and `logs`.
- `[run].agent` is the import path used by worker startup; authoring that class belongs in the custom workflow sub-skill.

## State and log layout

If `AREAL_HOME` is unset, the CLI uses `~/.areal`.

| Namespace | Service state | Extra state | Logs | Current pointer |
|---|---|---|---|---|
| Inference | `$AREAL_HOME/inf/services/<service>.json` | `$AREAL_HOME/inf/models/<service>.json` | `$AREAL_HOME/inf/logs/<service>/*.log` | `$AREAL_HOME/inf/current-service` |
| Agent | `$AREAL_HOME/agent/services/<service>.json` | none | `$AREAL_HOME/agent/logs/<service>/*.log` | `$AREAL_HOME/agent/current-service` |

Service name resolution order is: explicit `--service`, current-service pointer, the single known service if exactly one exists, then `default`.

`run --force` first tries an orderly state load. If state parsing fails, it walks raw JSON for `pid`/`pids` keys and kills recovered PIDs before removing state. For inference, raw recovery walks both service-state and model-state files.

## Direct service module entrypoints

Direct modules are useful for controller internals and carefully bounded debugging. They start servers and should not be used as validation commands.

### Inference service modules

```bash
python -m areal.v2.inference_service.router \
  --host 127.0.0.1 --port 8081 \
  --admin-api-key "$INF_ADMIN_KEY" \
  --routing-strategy round_robin

python -m areal.v2.inference_service.gateway \
  --host 127.0.0.1 --port 8080 \
  --admin-api-key "$INF_ADMIN_KEY" \
  --router-addr http://127.0.0.1:8081

python -m areal.v2.inference_service.data_proxy \
  --host 127.0.0.1 --port 8082 \
  --backend-addr http://127.0.0.1:30000 \
  --backend-type sglang \
  --tokenizer-path /models/qwen \
  --admin-api-key "$INF_ADMIN_KEY"
```

Data-proxy tuning flags include `--request-timeout`, `--set-reward-finish-timeout`, `--callback-server-addr`, `--tool-call-parser`, `--reasoning-parser`, `--engine-max-tokens`, and `--chat-template-type {hf,concat}`.

### Agent service modules

```bash
python -m areal.v2.agent_service.router \
  --host 127.0.0.1 --port 8081 \
  --admin-api-key "$AGENT_ADMIN_KEY"

python -m areal.v2.agent_service.gateway \
  --host 127.0.0.1 --port 8080 \
  --router-addr http://127.0.0.1:8081 \
  --admin-api-key "$AGENT_ADMIN_KEY"

python -m areal.v2.agent_service.worker \
  --host 127.0.0.1 --port 9000 \
  --agent my_project.agents.MathAgent

python -m areal.v2.agent_service.data_proxy \
  --host 127.0.0.1 --port 9100 \
  --worker-addr http://127.0.0.1:9000
```

The high-level `areal agent run` command is usually safer because it launches a consistent gateway/router/worker/data-proxy stack and persists state for status/logs/stop.

### Training service modules

The v2 training service exposes gateway/router/data-proxy/worker processes used by controllers. The operator-facing CLI for most users remains `areal train run`.

```bash
python -m areal.v2.training_service.router \
  --host 127.0.0.1 --port 9081 \
  --admin-api-key "$TRAIN_ADMIN_KEY"

python -m areal.v2.training_service.gateway \
  --host 127.0.0.1 --port 9080 \
  --router-addr http://127.0.0.1:9081 \
  --admin-api-key "$TRAIN_ADMIN_KEY"

python -m areal.v2.training_service.worker \
  --host 127.0.0.1 --port 30000 \
  --admin-api-key "$TRAIN_ADMIN_KEY"

python -m areal.v2.training_service.data_proxy \
  --host 127.0.0.1 --port 9082 \
  --worker-addrs http://127.0.0.1:30000 \
  --admin-api-key "$TRAIN_ADMIN_KEY"
```

Training gateway forwards these engine endpoints to the routed training worker/data-proxy: `/train_batch`, `/forward_batch`, `/eval_batch`, `/train`, `/eval`, `/set_version`, `/get_version`, `/save`, `/load`, `/offload`, `/onload`, `/step_lr_scheduler`, `/optimizer_zero_grad`, `/optimizer_step`, `/get_device_stats`, `/config_perf_tracer`, `/save_perf_tracer`, `/clear_batches`, `/export_stats`, `/sft/train`, `/sft/evaluate`, `/ppo/actor/compute_logp`, `/ppo/actor/compute_advantages`, `/ppo/actor/update`, `/ppo/critic/compute_values`, `/ppo/critic/update`, `/rw/train`, and `/rw/evaluate`.

## HTTP API summaries

### Inference gateway

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /health` | none | Gateway status and router address. |
| `POST /chat/completions`, `POST /v1/chat/completions` | admin key or valid session key routed by router | OpenAI-compatible chat completions. Streaming is relayed as SSE. |
| `GET /models`, `GET /v1/models` | admin key | List registered model names. |
| `POST /register_model` | admin key | Register internal data-proxy addresses or an external provider URL under a model name. |
| `POST /rl/start_session` | admin key | Create one or more session keys and register them in router state. Current response shape is `{"group_id": "...", "sessions": [{"session_id": "...", "session_api_key": "..."}]}`. |
| `POST /rl/set_reward` | session key, or admin key for HITL mode | Set a scalar reward for the active or selected interaction. |
| `POST /export_trajectories` | admin key | Export one or more sessions; optionally revokes router group state when `group_id` is supplied. |
| `POST /pause_generation/{worker_id}` and `/continue_generation/{worker_id}` | admin key | Pause/resume a specific worker through its data proxy. |
| `POST /release_memory_occupation/{worker_id}` and `/resume_memory_occupation/{worker_id}` | admin key | Offload/onload backend memory for a worker. |
| `POST /set_version/{worker_id}`, `GET /get_version/{worker_id}` | admin key | Set/get data-proxy model version. |

Session request and reward payloads:

```json
{"task_id": "task-001", "api_key": null, "group_size": 1}
```

```json
{"reward": 1.0, "interaction_id": null, "model": null}
```

```json
{"session_ids": ["task-001-0"], "group_id": "grp-...", "trajectory_id": null, "discount": 1.0, "style": "individual", "remove_session": true}
```

### Agent gateway/data-proxy/worker

The gateway routes to a data proxy by session key. The data proxy forwards a turn to a worker and either parses structured JSON events or relays raw passthrough bytes.

Worker request metadata can include `areal_inference` after the data proxy sees both `inf_base_url` and `session_api_key` in a turn body. The agent service does not call the inference service to mint keys; the caller must get the `sk-sess-*` key from the inference gateway first.

### Weight-update gateway

Start the gateway only when an AReaL controller or an operator has train/inference worker URLs ready:

```bash
python -m areal.v2.weight_update.gateway \
  --host 127.0.0.1 --port 7080 \
  --admin-api-key "$WEIGHT_ADMIN_KEY" \
  --init-timeout 300 \
  --update-timeout 120
```

Key endpoints:

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /health` | none | Gateway liveness. |
| `POST /connect` | admin key | Register a pair of train and inference worker URLs. Body includes `pair_name`, `train_worker_urls`, `inference_worker_urls`, optional `mode`, `save_path`, `use_lora`, `lora_name`, `lora_keep_versions`, `colocate`. |
| `POST /update_weights` | admin key | Push or load a specific version for a registered pair. Body: `pair_name`, `version`. |
| `POST /disconnect` | admin key | Tear down a registered pair. |
| `/weight_meta/{pair_name}/...` | admin key | Small key-value/set metadata store used by weight-update coordination. |

Weight-update notes:

- `mode="awex"` performs direct worker coordination. LoRA is rejected in `awex` mode; use disk mode for LoRA weight updates.
- `mode="disk"` requires an absolute `save_path` and, when `use_lora=true`, a non-empty `lora_name`.
- NCCL/HCCL and distributed transfer errors are backend issues; collect gateway logs and route to the distributed backend sub-skill.
