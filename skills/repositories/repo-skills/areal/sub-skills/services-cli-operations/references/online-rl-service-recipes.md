# Online RL And Service Recipes

These recipes cover AReaL 2.0 online RL service wiring, including inference gateway sessions, agent-service self-evolution, Hermes-style loops, rewards, and clean shutdown. They are command templates: replace placeholders and validate with `scripts/check_service_cli.py` before running.

## Key taxonomy

Keep these keys separate:

| Key | Owner | Used for |
|---|---|---|
| Inference admin key | AReaL training/inference gateway | `POST /rl/start_session`, `POST /export_trajectories`, model management, generation control. |
| Session API key (`sk-sess-*`) | Inference data proxy session | `/chat/completions`, `/v1/chat/completions`, `/rl/set_reward`, and self-evolution traffic from an agent. |
| Agent admin key | Agent service gateway/router | `areal agent run`, `POST /v1/responses`, `POST /sessions/close`, WebSocket token, internal route calls. |
| Actor/training admin key | Training/actor service | Training service and actor-side management; it is not a replacement for the inference session key. |
| Provider key | External LLM provider | Only for external upstream models or agents that call a provider directly. Never reuse it as an AReaL admin key. |

## Recipe 1: Online RL through an inference gateway

Use this when an AReaL training job is already configured for online rollout capture and prints or otherwise exposes an inference gateway address.

### 1. Configure training for online mode

In the experiment YAML, ensure the rollout agent settings are present:

```yaml
rollout:
  agent:
    mode: online
    admin_api_key: "${INF_ADMIN_KEY}"
    session_timeout_seconds: 3600
    turn_discount: 1.0
    export_style: individual
    drop_retry_orphans: false
```

Operational notes:

- Online mode is for external users, evaluators, or agent runtimes that drive HTTP requests.
- The training job must be single-controller compatible and must expose an inference/proxy gateway.
- Scheduler and GPU/backend details are backend-planning concerns; if the gateway fails during worker launch, route to the distributed backend sub-skill.

A generic driver invocation shape is:

```bash
areal train run \
  --config /path/to/online-rl.yaml \
  --driver my_project.train:main \
  experiment_name=my-exp trial_name=trial-0 \
  rollout.backend=sglang:d1 actor.backend=fsdp:d1 \
  rollout.agent.admin_api_key="$INF_ADMIN_KEY"
```

This starts training; do not run it unless the user explicitly wants a live training job.

### 2. Start one or more inference sessions

```bash
curl -sS -X POST "$INF_GATEWAY/rl/start_session" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $INF_ADMIN_KEY" \
  -d '{"task_id":"demo-task","group_size":1}'
```

Current response shape:

```json
{
  "group_id": "grp-...",
  "sessions": [
    {"session_id": "demo-task-0", "session_api_key": "sk-sess-..."}
  ]
}
```

Extract:

```bash
export GROUP_ID='grp-...'
export SESSION_ID='demo-task-0'
export SESSION_API_KEY='sk-sess-...'
```

For grouped rollouts, set `group_size` above 1 and use every returned `session_api_key` for one trajectory in the group.

### 3. Interact through the gateway

OpenAI-compatible chat completions:

```bash
curl -sS -X POST "$INF_GATEWAY/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $SESSION_API_KEY" \
  -d '{
    "model": "default",
    "messages": [{"role":"user","content":"What is 12 * 15 + 3?"}],
    "temperature": 0.7,
    "top_p": 1.0
  }'
```

Equivalent non-`/v1` path:

```bash
curl -sS -X POST "$INF_GATEWAY/chat/completions" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $SESSION_API_KEY" \
  -d '{"model":"default","messages":[{"role":"user","content":"hello"}]}'
```

Python client shape:

```python
from openai import OpenAI

client = OpenAI(base_url=f"{INF_GATEWAY}/v1", api_key=SESSION_API_KEY)
resp = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "hello"}],
)
print(resp.choices[0].message.content)
```

### 4. Set a reward

Set a scalar reward on the most recent interaction:

```bash
curl -sS -X POST "$INF_GATEWAY/rl/set_reward" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $SESSION_API_KEY" \
  -d '{"reward":1.0,"interaction_id":null}'
```

Use `interaction_id` only when assigning reward to a specific interaction. Keep reward ranges bounded for the training recipe; many AReaL online examples use `[-1, 1]`.

### 5. Export or refresh

For offline-style export after reward:

```bash
curl -sS -X POST "$INF_GATEWAY/export_trajectories" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $INF_ADMIN_KEY" \
  -d '{
    "session_ids":["'"$SESSION_ID"'"],
    "group_id":"'"$GROUP_ID"'",
    "discount":1.0,
    "style":"individual",
    "remove_session":true
  }'
```

For persistent online/HITL loops, repeated `set_reward` calls can mark trajectories ready; the controller may export through callbacks. If reusing a prior API key, `start_session` accepts `api_key`, but a key bound to an active unfinished session can return `409`.

## Recipe 2: Standalone inference service with model registration

Use this for local inference service operation separate from a trainer.

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
  --model-path /models/qwen \
  --tokenizer-path /models/qwen \
  --engine-args '--mem-fraction-static 0.85' \
  --proxy-args '--request-timeout 120 --chat-template-type hf'

areal inf status --service inf-demo
areal inf models --service inf-demo
```

Then call:

```bash
curl -sS -X POST 'http://127.0.0.1:8080/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $INF_ADMIN_KEY" \
  -d '{"model":"qwen","messages":[{"role":"user","content":"hello"}]}'
```

Shutdown:

```bash
areal inf stop --service inf-demo --grace 10
```

If registration fails after worker start, inspect `areal inf logs --component gateway`, `router`, `<model>-worker-<rank>`, and `<model>-data-proxy-<rank>`. Backend launch errors route to the distributed backend sub-skill.

## Recipe 3: Agent service plain serving

Use this when a pluggable agent class is importable and you only need the agent service, not training capture.

```bash
areal agent run \
  --service agent-demo \
  --agent my_project.agents.MathAgent \
  --num-pairs 1 \
  --admin-api-key "$AGENT_ADMIN_KEY"
```

Call the Responses-compatible path:

```bash
curl -sS -X POST "$AGENT_GATEWAY/v1/responses" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $AGENT_ADMIN_KEY" \
  -H 'X-AReaL-Session-Key: agent-session-1' \
  -d '{
    "model":"agent-model",
    "input":[{"type":"message","content":"Explain policy gradients briefly"}],
    "user":"operator-1"
  }'
```

Or the chat-completions path:

```bash
curl -sS -X POST "$AGENT_GATEWAY/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -H 'X-AReaL-Session-Key: chat-session-1' \
  -d '{
    "model":"agent-model",
    "user":"operator-1",
    "messages":[{"role":"user","content":"hello"}],
    "stream":true
  }'
```

Notes:

- `/v1/responses` is agent-admin-key protected.
- `/v1/chat/completions` requires route affinity through `X-AReaL-Session-Key` or `user`; it is not protected by the agent admin dependency at the gateway, so deploy it behind your own network controls when needed.
- The gateway echoes `X-AReaL-Session-Key`; reuse that value for later turns.
- Close stale sessions explicitly:

  ```bash
  curl -sS -X POST "$AGENT_GATEWAY/sessions/close" \
    -H 'Content-Type: application/json' \
    -H "Authorization: Bearer $AGENT_ADMIN_KEY" \
    -d '{"session_key":"agent-session-1"}'
  ```

## Recipe 4: Agent service self-evolution through an inference gateway

Use this when an external or in-process agent should route its internal LLM calls through AReaL's inference gateway so the trajectory can be rewarded and trained.

### 1. Prepare both services

- An inference/training gateway is running and reachable at `$INF_GATEWAY`.
- An agent service is running and reachable at `$AGENT_GATEWAY`.
- A session key has been minted by the inference gateway using Recipe 1.

### 2. Send inference-routing fields to the agent turn

Responses path:

```bash
curl -sS -X POST "$AGENT_GATEWAY/v1/responses" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $AGENT_ADMIN_KEY" \
  -H 'X-AReaL-Session-Key: agent-session-1' \
  -d '{
    "model":"agent-model",
    "input":[{"type":"message","content":"Solve the task with tools"}],
    "user":"operator-1",
    "inf_base_url":"'"$INF_GATEWAY"'/v1",
    "inf_model":"default",
    "session_api_key":"'"$SESSION_API_KEY"'"
  }'
```

Chat-completions path:

```bash
curl -sS -X POST "$AGENT_GATEWAY/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -H 'X-AReaL-Session-Key: chat-session-1' \
  -d '{
    "model":"agent-model",
    "user":"operator-1",
    "messages":[{"role":"user","content":"Use your tools and answer"}],
    "inf_base_url":"'"$INF_GATEWAY"'/v1",
    "inf_model":"default",
    "session_api_key":"'"$SESSION_API_KEY"'"
  }'
```

The agent data proxy caches `inf_base_url`, `session_api_key`, and optional `inf_model` on the session. Later turns in the same agent session may omit the fields; the data proxy injects the cached handle into worker metadata as `areal_inference`.

If either `inf_base_url` or `session_api_key` is present without the other, the data proxy rejects the turn with `400`. This is intentional; the agent service never mints or retrieves inference session keys itself.

### 3. Reward the inference session

```bash
curl -sS -X POST "$INF_GATEWAY/rl/set_reward" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $SESSION_API_KEY" \
  -d '{"reward":1.0}'
```

## Recipe 5: Hermes-style online RL loop

Hermes-style operation is a special case of Recipe 4: a dedicated agent class runs in the agent service, while its internal LLM calls are routed to the inference gateway using a per-episode `sk-sess-*` key.

### Operator sequence

1. Start or connect to the online training job and record the inference gateway URL:

   ```bash
   export INF_GATEWAY='http://127.0.0.1:8090'
   export INF_ADMIN_KEY='replace-with-inference-admin-key'
   ```

2. Start the Hermes-compatible agent service with an importable agent class:

   ```bash
   areal agent run \
     --service hermes \
     --agent my_project.hermes.HermesAgent \
     --num-pairs 1 \
     --admin-api-key "$AGENT_ADMIN_KEY"
   ```

3. Start a new inference session for the episode:

   ```bash
   curl -sS -X POST "$INF_GATEWAY/rl/start_session" \
     -H 'Content-Type: application/json' \
     -H "Authorization: Bearer $INF_ADMIN_KEY" \
     -d '{"task_id":"hermes-episode","group_size":1}'
   ```

4. Interact with the agent service and include the inference-routing fields:

   ```bash
   curl -sS -X POST "$AGENT_GATEWAY/v1/responses" \
     -H 'Content-Type: application/json' \
     -H "Authorization: Bearer $AGENT_ADMIN_KEY" \
     -H 'X-AReaL-Session-Key: hermes-agent-session' \
     -d '{
       "model":"hermes-agent",
       "input":[{"type":"message","content":"Your task here"}],
       "user":"operator-1",
       "inf_base_url":"'"$INF_GATEWAY"'/v1",
       "inf_model":"default",
       "session_api_key":"'"$SESSION_API_KEY"'"
     }'
   ```

5. Score the episode on the inference gateway using the same session key:

   ```bash
   curl -sS -X POST "$INF_GATEWAY/rl/set_reward" \
     -H 'Content-Type: application/json' \
     -H "Authorization: Bearer $SESSION_API_KEY" \
     -d '{"reward":1.0}'
   ```

6. Start a fresh inference session for the next episode, or refresh only when the previous session has been finalized/exported.

### Hermes wiring pitfalls

- The inference gateway admin key starts sessions; the session key scores and routes the episode.
- The agent admin key authorizes the agent service gateway; it does not authorize inference reward endpoints.
- If the agent also has external provider fallback credentials, keep those in provider-specific environment variables and do not put them in AReaL config/state.
- If the Hermes or framework agent import path fails, fix the agent class under the custom workflow sub-skill. If the inference backend fails to launch or update weights, route to the distributed backend sub-skill.

## Recipe 6: Controlled shutdown and cleanup

Always stop high-level CLI-managed services through their CLI first so state files and current-service pointers are cleaned consistently.

```bash
areal agent status --service agent-demo
areal agent logs --service agent-demo --component gateway --lines 100
areal agent stop --service agent-demo --grace-period 10

areal inf status --service inf-demo
areal inf logs --service inf-demo --component gateway --lines 100
areal inf stop --service inf-demo --grace 10
```

Use `--force` only when graceful shutdown fails or stale/corrupt state is blocking a fresh launch. Use `--keep-state` only when you need to preserve the files for forensic inspection.

## Safe dry-run validation examples

```bash
python scripts/check_service_cli.py \
  --command 'areal agent run --service hermes --agent my_project.hermes.HermesAgent --num-pairs 1 --admin-api-key $AGENT_ADMIN_KEY'

python scripts/check_service_cli.py \
  --command 'areal inf register --model-name qwen --backend vllm:d2t4 --model-path /models/qwen --engine-args "--gpu-memory-utilization 0.90"'

python scripts/check_service_cli.py \
  --backend sglang:d1 \
  --proxy-args '--request-timeout 120 --chat-template-type hf'
```
