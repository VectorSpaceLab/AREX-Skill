# Model Backends, Credentials, And Budget

## When To Read

Read this before constructing `SocialAgent` objects that may execute
`LLMAction()`, before selecting OpenAI/VLLM/DeepSeek/CAMEL backends, or before
scaling a simulation beyond a tiny manual smoke.

## How Models Enter OASIS

OASIS delegates LLM calls to CAMEL. Pass the model object to each
`SocialAgent`, or pass it to `generate_reddit_agent_graph(...)` /
`generate_twitter_agent_graph(...)` so generated agents share that backend.
The model value can be:

- a CAMEL `BaseModelBackend`,
- a list of CAMEL model backends, or
- a CAMEL `ModelManager` for scheduling/load balancing.

If `model=None`, current CAMEL behavior may create a default OpenAI backend.
That means even a manual-only `SocialAgent` construction can require a non-empty
`OPENAI_API_KEY`. A non-secret placeholder is acceptable only for no-LLM smoke
runs that never execute `LLMAction`. Real `LLMAction` requires real provider
credentials, a budget, and a tool/function-calling-capable model.

## OpenAI Or OpenAI-Compatible Provider

```python
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O_MINI,
)
```

Before creating the model, set the provider credentials in the process
environment, for example `OPENAI_API_KEY`. If the user uses a proxy or
OpenAI-compatible endpoint, set the base URL variable expected by CAMEL for that
backend before model construction. Keep keys out of code, logs, and generated
skill files.

## VLLM Or Local OpenAI-Compatible Server

Use VLLM/local servers when the user has already deployed a tool-call-capable
OpenAI-compatible endpoint:

```python
from camel.models import ModelFactory, ModelManager
from camel.types import ModelPlatformType

vllm_a = ModelFactory.create(
    model_platform=ModelPlatformType.VLLM,
    model_type="qwen-2",
    url="http://localhost:8000/v1",
)
vllm_b = ModelFactory.create(
    model_platform=ModelPlatformType.VLLM,
    model_type="qwen-2",
    url="http://localhost:8001/v1",
)
models = ModelManager(models=[vllm_a, vllm_b], scheduling_strategy="round_robin")
```

Operational checks before using `LLMAction`:

- the server is reachable and exposes a `/v1`-style API;
- the served model name matches `model_type`;
- the model/server supports tool calling or function calling;
- the server capacity matches the chosen `semaphore` and number of active
  agents;
- any GPU/model download/cache requirement has been approved by the user.

## DeepSeek Via CAMEL

OASIS examples use CAMEL's DeepSeek platform with an explicit endpoint:

```python
from camel.models import ModelFactory
from camel.types import ModelPlatformType

model = ModelFactory.create(
    model_platform=ModelPlatformType.DEEPSEEK,
    model_type="deepseek-chat",
    url="https://api.deepseek.com/v1",
)
```

Set the DeepSeek credential variable expected by CAMEL in the runtime
environment before constructing the model. Treat DeepSeek exactly like any real
provider: run the manual smoke first, start with a small activated subset, set a
low `semaphore`, and confirm budget.

## Multiple Models Or Per-Agent Backends

For heterogeneous runs, either instantiate each `SocialAgent` with a different
model or pass a `ModelManager` to generated agents. Restrict `available_actions`
so lower-capability models are not asked to use unsupported tools.

```python
agent = SocialAgent(
    agent_id=0,
    user_info=user_info,
    agent_graph=agent_graph,
    model=models,
    available_actions=[ActionType.CREATE_POST, ActionType.FOLLOW],
)
```

## Budget Checklist

Before a provider-backed run:

1. Confirm the provider/API key or local server is available.
2. Confirm the selected model supports tool/function calling.
3. Run [the manual smoke](../scripts/oasis_manual_smoke.py) or an equivalent
   no-provider check.
4. Activate only a small subset of agents for the first `LLMAction` step.
5. Set `semaphore` to a provider-safe value.
6. Estimate tokens as a product of agent count, activation probability, time
   steps, environment prompt size, and expected output length. Public OASIS
   cost notes show that even a 100-agent, one-step run can consume hundreds of
   thousands of input tokens.
7. Log the chosen stop condition: max steps, max active agents, max token/cost,
   or manual abort.

If credentials are missing or budget is unclear, switch to manual actions or
stop with a clear blocked reason instead of running `LLMAction()`.
