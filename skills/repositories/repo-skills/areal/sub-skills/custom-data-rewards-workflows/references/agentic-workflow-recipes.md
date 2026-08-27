# Agentic Workflow Recipes

This reference covers AReaL's agent, multi-turn, tool-use, VLM, and OpenAI-compatible integration contracts. It intentionally omits service startup and training-launch details; route those to sibling sub-skills when needed.

## 1. Choose the integration style

| Situation | Recommended style | Why |
|---|---|---|
| New agent code can call an OpenAI- or Anthropic-compatible API | Proxy agent workflow | Keeps agent code independent from AReaL internals and lets AReaL capture token/logprob data. |
| Existing framework accepts `base_url` and `api_key` | Proxy agent workflow | Usually only configuration changes are needed. |
| Framework requires a concrete custom OpenAI client object | Legacy direct `ArealOpenAI` inside a `RolloutWorkflow` | Provides direct engine calls but couples code to AReaL. Do not choose proactively. |
| Workflow emits tensors directly, uses custom tools, or needs full control over `loss_mask` | Custom `RolloutWorkflow` | Best for TIR/scaffolding-style workflows where tool outputs must be masked. |
| External users interact through online sessions | Proxy `mode: online` | Requires service/session lifecycle. Route setup and operation to `services-cli-operations`. |

## 2. Proxy agent workflow: preferred pattern

Any importable class with an async `run()` method can be wrapped by AReaL. Inheriting from `AgentWorkflow` is deprecated and unnecessary.

```python
import os
from openai import AsyncOpenAI

class MyAgent:
    async def run(self, data: dict, **extra_kwargs) -> float | dict[str, float]:
        http_client = extra_kwargs.get("http_client")
        base_url = extra_kwargs.get("base_url") or os.getenv("OPENAI_BASE_URL")
        api_key = extra_kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")

        client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            http_client=http_client,
            max_retries=0,
        )
        response = await client.chat.completions.create(
            model="default",
            messages=data["messages"],
        )
        return score(response.choices[0].message.content, data["answer"])
```

Required method contract:

```python
async def run(self, data: dict, **extra_kwargs) -> float | dict[str, float]
```

Injected `extra_kwargs`:

| Key | Type | Meaning |
|---|---|---|
| `base_url` | `str` | AReaL proxy worker base URL. Use this for model calls. |
| `api_key` | `str` | Session-scoped key for the current rollout. |
| `http_client` | `httpx.AsyncClient` | Shared async HTTP client. Reuse it to avoid per-call connection overhead. |

Reward return rules:

- Return `float` to reward the latest captured completion/response.
- Return `dict[str, float]` to assign rewards by completion/response ID for multi-turn or branching conversations.
- Use `response.id` from OpenAI chat/responses objects as the dict key.
- Do not return tensors, lists, dataclasses, or coroutine objects.

## 3. Agent config fields

Agent workflow settings live under `rollout.agent` in AReaL configs:

```yaml
rollout:
  agent:
    agent_cls_path: my_package.agents.MyAgent
    mode: inline
    turn_discount: 0.9
    export_style: individual
    tool_call_parser: qwen25
    reasoning_parser: qwen3
    chat_template_type: hf
    subproc_max_workers: 4
    drop_retry_orphans: false
```

Common fields:

| Field | Values/default | Use |
|---|---|---|
| `agent_cls_path` | import path | Used by service/controller config paths. Must be non-empty when constructing `AgentConfig`. |
| `mode` | `inline`, `subproc`, `online` | Execution mode. `online` needs service/session lifecycle. |
| `turn_discount` | float, default `1.0` | Geometric reward discount for parent interactions. |
| `export_style` | `individual`, `concat` | `individual` exports each interaction; `concat` exports leaf conversations only. |
| `tool_call_parser` | e.g. `qwen`, `qwen25`, `qwen3_coder`, `hermes`, `llama3_json`, `mistral`, `openai`, `deepseek_v3` | Parser used when model output encodes tool calls. Backend support may vary. |
| `reasoning_parser` | e.g. `qwen3` | Handles reasoning blocks such as `<think>...</think>`. |
| `chat_template_type` | `hf`, `concat` | `concat` can preserve multi-turn prefix tokens but is stricter. |
| `subproc_max_workers` | integer | Process pool size in subprocess mode. |
| `drop_retry_orphans` | bool | Drops interactions caused by upstream SDK retries before export. Useful with timeouts/retries. |
| `session_timeout_seconds` | integer | Stale session cleanup; service operation belongs in `services-cli-operations`. |

Trainer invocation, config merging, scheduler fields, and backend allocation should be handled by `post-training-experiments` and `distributed-engines-backends`.

## 4. Inline vs subprocess mode

| Mode | How it runs | Use when | Requirements |
|---|---|---|---|
| `inline` | Calls `await agent.run(...)` in the rollout worker process. | Agent is async-friendly and imports cleanly. | Use async clients and avoid blocking CPU/file/network work. |
| `subproc` | Runs `agent.run(data)` in a process pool with `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_BASE_URL`, and `ANTHROPIC_API_KEY` set. | Agent depends on sync libraries, blocking framework code, or process isolation. | Agent instance and data must be picklable; no shared `http_client`. |
| `online` | Waits for an external session to complete through a proxy gateway. | Human/agent-service online RL sessions. | Requires lifecycle commands, session keys, and gateway operation; route to `services-cli-operations`. |

Subprocess-mode skeleton with a sync client inside async `run()`:

```python
import os
from openai import OpenAI

class MySyncAgent:
    async def run(self, data, **extra_kwargs):
        client = OpenAI(
            base_url=os.environ["OPENAI_BASE_URL"],
            api_key=os.environ["OPENAI_API_KEY"],
        )
        response = client.chat.completions.create(
            model="default",
            messages=data["messages"],
        )
        return score(response.choices[0].message.content, data["answer"])
```

## 5. Workflow resolution behavior

When a workflow is passed to rollout/training code, AReaL resolves it as follows:

1. `RolloutWorkflow` instance: use it directly.
2. `RolloutWorkflow` class: instantiate with `workflow_kwargs`.
3. Dotted string path: import the object, then apply rules 1/2/4.
4. Non-`RolloutWorkflow` class or instance: treat as an agent and wrap in `OpenAIProxyWorkflow`; proxy workers must be available.
5. `workflow=None` is valid only for configured online mode.
6. If `group_size > 1`, wrap the resolved workflow in grouped rollout.

Validation command:

```bash
python scripts/check_workflow_contract.py --workflow my_package.agents.MyAgent --mode agent
```

## 6. Legacy direct `ArealOpenAI` pattern

Use only when a framework requires a custom OpenAI client object and cannot be configured with `base_url`/`api_key`.

```python
from areal.api import RolloutWorkflow
from areal.experimental.openai import ArealOpenAI

class MyDirectWorkflow(RolloutWorkflow):
    def __init__(self, tokenizer, turn_discount=0.9):
        self.tokenizer = tokenizer
        self.turn_discount = turn_discount

    async def arun_episode(self, engine, data):
        client = ArealOpenAI(engine=engine, tokenizer=self.tokenizer)
        response = await client.chat.completions.create(
            model="default",
            messages=data["messages"],
        )
        reward = score(response.choices[0].message.content, data["answer"])
        client.set_last_reward(float(reward))
        client.apply_reward_discount(turn_discount=self.turn_discount)
        return client.export_interactions(style="individual")
```

Direct-client methods to know:

| Method | Use |
|---|---|
| `chat.completions.create(...)` | OpenAI-compatible chat completion. |
| `responses.create(...)` | OpenAI Responses API shape. |
| `set_reward(id, reward)` | Set reward for a specific interaction. |
| `set_last_reward(reward)` | Set reward for latest interaction. |
| `apply_reward_discount(turn_discount)` | Back-propagate rewards through parent-child interactions. |
| `export_interactions(style)` | Return `dict[str, InteractionWithTokenLogpReward]` for training. |

## 7. Multi-turn reward assignment

For proxy agents, return a reward map when more than the last model call should be explicitly rewarded:

```python
class MultiTurnAgent:
    async def run(self, data, **extra_kwargs):
        client = make_async_openai_client(extra_kwargs)
        messages = list(data["messages"])
        rewards = {}
        for _ in range(3):
            response = await client.chat.completions.create(
                model="default",
                messages=messages,
            )
            message = response.choices[0].message
            messages.append(message.model_dump(exclude_none=True))
            r = score(message.content, data["answer"])
            rewards[response.id] = float(r)
            if r == 1.0:
                break
            messages.append({"role": "user", "content": "Try again and give a parsable final answer."})
        return rewards
```

Reward propagation:

- `turn_discount=1.0`: earlier turns receive the same propagated downstream reward.
- `turn_discount<1.0`: parent turns receive geometrically discounted child rewards.
- `export_style=individual`: each interaction becomes its own training item.
- `export_style=concat`: only leaf/merged trajectories are exported; use only for linear conversations with token-consistent prefixes.
- If the upstream SDK retries model calls and creates unobserved interactions, set `drop_retry_orphans=true` after confirming retries are the cause.

## 8. Tool-call workflows

### Proxy/tool schema path

If the model backend and parser support OpenAI tool calling, pass OpenAI-compatible tool specs to the client:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate an arithmetic expression.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    }
]
response = await client.chat.completions.create(
    model="default",
    messages=data["messages"],
    tools=tools,
    tool_choice="auto",
)
```

Tool parser notes:

- Choose `rollout.agent.tool_call_parser` to match model/backend output format.
- Qwen-style parser names include `qwen`, `qwen25`, `qwen3`, `qwen3_xml`, and `qwen3_coder`.
- Some parser functionality is provided by the inference backend packages. If a parser import fails, route backend package/runtime issues to `distributed-engines-backends`.
- The qwen3-coder XML form supports `<tool_call><function=Name><parameter=arg>...</parameter></function></tool_call>` and coerces simple JSON-schema scalar types when possible.

### Custom tensor workflow path

For tool-integrated reasoning where the workflow executes tools itself:

- Subclass `RolloutWorkflow`.
- Generate until a tool-start marker, then continue until the matching end marker.
- Execute tools asynchronously and clean up sandboxes/resources in `finally`.
- Append tool output to context with `loss_mask=0`, `logprobs=0.0`, and `versions=-1`.
- Keep generated model tokens at `loss_mask=1`.
- Record tool metrics through AReaL stats tracking if available.
- Route sandbox service deployment or remote execution failures to `services-cli-operations` or external platform docs, not this sub-skill.

## 9. VLM agent requests

For direct `VisionRLVRWorkflow`, use the row contract in `data-reward-workflow-contracts.md`: `messages`, `images`, and optional `messages_chat` placeholder.

For proxy agent VLM calls, use OpenAI-compatible content parts with actual image URLs or data URIs:

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
            {"type": "text", "text": "Answer the visual question."},
        ],
    }
]
response = await client.chat.completions.create(model="default", messages=messages)
```

Rules:

- Empty `image_url.url` is valid only as a placeholder in the direct `VisionRLVRWorkflow` path where `image_data` is supplied separately.
- Proxy OpenAI calls must provide a non-empty image URL or base64 data URI because the proxy extracts image data from the request.
- The VLM processor/backend determines whether `mm_token_type_ids`, `image_grid_thw`, or only `pixel_values` are present.
- Tokenization/image-processing backend errors route to `distributed-engines-backends` if they involve SGLang/vLLM/worker compatibility.

## 10. Framework integration notes

| Framework style | Integration advice |
|---|---|
| Plain OpenAI SDK | Prefer proxy mode with `AsyncOpenAI(base_url=..., api_key=..., http_client=..., max_retries=0)`. |
| Anthropic SDK | Proxy supports Anthropic-style messages. Use injected `base_url`/`api_key`; keep `run()` async. |
| OpenAI Agents SDK | Prefer a provider/client configured against proxy if supported. If the SDK requires an `openai_client` object, use direct `ArealOpenAI` inside `RolloutWorkflow`. |
| CAMEL-like model wrappers | If the wrapper accepts an OpenAI-compatible base URL, use proxy. If it requires a custom model/client object, use direct `ArealOpenAI`. |
| LangChain-style chains | Use async clients/callbacks in inline mode; move sync chains to subprocess mode. |
| Scaffolding/pipeline agents | Wrap the pipeline as `RolloutWorkflow` if it must emit tensor dicts and control loss masks. |
| SWE/Tau2/sandbox agents | Ensure agent package, datasets, simulator/sandbox URLs, and environment variables are available on every worker. Route external service setup and backend failures away from this sub-skill. |

## 11. Safe preflight snippets

Check an agent class import and sample data:

```bash
python scripts/check_workflow_contract.py \
  --workflow my_package.agents.MyAgent \
  --sample-json sample.json \
  --mode agent
```

Check a VLM proxy sample for image URL mistakes:

```bash
python scripts/check_workflow_contract.py \
  --sample-json vlm_agent_sample.json \
  --mode agent \
  --require messages
```

Check a direct VisionRLVR sample:

```bash
python scripts/check_workflow_contract.py \
  --sample-json vision_rlvr_sample.json \
  --mode vision-rlvr \
  --require answer
```
