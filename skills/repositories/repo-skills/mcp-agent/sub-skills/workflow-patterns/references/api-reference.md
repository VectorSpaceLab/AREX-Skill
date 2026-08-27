# Workflow API Reference

This reference captures current mcp-agent workflow imports and constructor/helper surfaces. Prefer factory helpers for application code, and use direct classes when you need explicit control.

## Common Imports

```python
from mcp_agent.app import MCPApp
from mcp_agent.workflows.factory import (
    AgentSpec,
    OrchestratorOverrides,
    RequestParams,
    create_deep_orchestrator,
    create_evaluator_optimizer_llm,
    create_intent_classifier_embedding,
    create_intent_classifier_llm,
    create_llm,
    create_orchestrator,
    create_parallel_llm,
    create_router_embedding,
    create_router_llm,
    create_swarm,
)
from mcp_agent.workflows.evaluator_optimizer.evaluator_optimizer import QualityRating
from mcp_agent.workflows.intent_classifier.intent_classifier_base import Intent
```

`RequestParams` is re-exported by `mcp_agent.workflows.factory` and is defined in `mcp_agent.workflows.llm.augmented_llm`. Useful fields include `model`, `maxTokens`, `temperature`, `use_history`, `max_iterations`, `parallel_tool_calls`, and `strict`.

## Provider Names

- LLM providers accepted by factory helpers: `openai`, `anthropic`, `azure`, `google`, `bedrock`, `ollama` where supported by the specific helper.
- LLM routing providers with direct provider wrappers: `openai`, `anthropic`; other LLM providers go through generic `LLMRouter.create(...)` with an LLM factory.
- Embedding providers: `openai`, `cohere`.
- Swarm factory providers: `openai`, `anthropic`.

Provider default models may instantiate API clients immediately. Import checks can be done without creating provider clients; actual runtime requires optional provider packages and configured API keys.

## Agents and LLMs

```python
AgentSpec(
    name="researcher",
    instruction="Search sources and extract verifiable facts.",
    server_names=["fetch"],
)
```

Factory helpers usually accept `AgentSpec`, instantiated `Agent`, or an existing `AugmentedLLM`. Existing `AugmentedLLM` instances are useful when you want to reuse an attached model or pass one workflow as a worker to another.

### `create_llm(...)`

```python
llm = create_llm(
    agent=AgentSpec(name="writer", instruction="Write concise answers."),
    provider="openai",
    model="gpt-4o-mini",
    request_params=RequestParams(temperature=0.2),
    context=running_app.context,
)
```

It wraps an `Agent` or `AgentSpec` in a provider `AugmentedLLM`.

## LLM Router

Correct class name: `LLMRouter`. Do not use `RouterLLM`.

Direct import:

```python
from mcp_agent.workflows.router.router_llm import LLMRouter, LLMRouterResult
```

Factory:

```python
router = await create_router_llm(
    name="support_router",
    server_names=["filesystem"],
    agents=[AgentSpec(name="writer", instruction="Draft user-facing responses.")],
    functions=[fallback_function],
    routing_instruction="Prefer agents for tool use; prefer functions for trivial fallbacks.",
    provider="openai",
    model=None,
    request_params=RequestParams(temperature=0),
    context=running_app.context,
)
```

Direct constructor/factory shape:

```python
router = await LLMRouter.create(
    name="support_router",
    llm_factory=lambda agent, **kw: SomeAugmentedLLM(agent=agent, instruction=kw.get("instruction")),
    server_names=["filesystem"],
    agents=[agent_or_llm],
    functions=[callable_destination],
    routing_instruction=None,
    context=running_app.context,
)
```

Methods:

- `await router.route(request: str, top_k: int = 1)` returns `list[LLMRouterResult]` across enabled destination categories.
- `await router.route_to_agent(request, top_k=1)` returns agent/LLM destinations only.
- `await router.route_to_server(request, top_k=1)` returns server-name destinations only.
- `await router.route_to_function(request, top_k=1)` returns callable destinations only.
- `await router.generate_str(message)` routes to the best downstream agent/LLM and delegates generation. Use this only when routed destinations are executable as LLMs; callables/servers need explicit handling.

`LLMRouterResult` guarantees `result`, `confidence`, and optional `reasoning`. It does not expose a stable public `category` field. If destination type matters, use `route_to_*` helpers or inspect `result` with `isinstance` / `callable`.

## Embedding Router

Direct import:

```python
from mcp_agent.workflows.router.router_embedding import EmbeddingRouter
from mcp_agent.workflows.embedding.embedding_openai import OpenAIEmbeddingModel
from mcp_agent.workflows.embedding.embedding_cohere import CohereEmbeddingModel
```

Factory:

```python
router = await create_router_embedding(
    provider="openai",  # or "cohere"
    model=None,         # optional EmbeddingModel instance
    agents=[AgentSpec(name="billing", instruction="Handle billing questions.")],
    functions=[fallback_function],
    context=running_app.context,
)
```

Direct constructor/factory shape:

```python
router = await EmbeddingRouter.create(
    embedding_model=OpenAIEmbeddingModel(model="text-embedding-3-small", context=running_app.context),
    server_names=None,
    agents=[agent_or_llm],
    functions=[callable_destination],
    context=running_app.context,
)
```

Methods mirror router methods. Results use `RouterResult` with `result` and `p_score`.

## Intent Classifiers

```python
from mcp_agent.workflows.intent_classifier.intent_classifier_base import Intent
from mcp_agent.workflows.intent_classifier.intent_classifier_llm import LLMIntentClassifier
from mcp_agent.workflows.intent_classifier.intent_classifier_embedding import EmbeddingIntentClassifier
```

Intent model:

```python
Intent(
    name="file_lookup",
    description="Open or summarize a local file through MCP tools.",
    examples=["show README", "open config", "summarize pyproject"],
    metadata={"risk": "low"},
)
```

LLM classifier factory:

```python
classifier = await create_intent_classifier_llm(
    intents=intents,
    provider="openai",  # or "anthropic"
    model=None,
    classification_instruction="Return one intent unless multiple are explicit.",
    name="intent_gate",
    request_params=RequestParams(temperature=0, strict=True),
    context=running_app.context,
)
results = await classifier.classify("show README.md", top_k=2)
```

Embedding classifier factory:

```python
classifier = await create_intent_classifier_embedding(
    intents=intents,
    provider="openai",  # or "cohere"
    model=None,
    context=running_app.context,
)
```

LLM results include `intent`, `confidence`, `p_score`, optional `reasoning`, and `extracted_entities`. Embedding results include `intent` and `p_score`.

## Parallel Fan-Out/Fan-In

Direct import:

```python
from mcp_agent.workflows.parallel.parallel_llm import ParallelLLM
from mcp_agent.workflows.parallel.fan_in import FanInInput
```

Factory:

```python
parallel = create_parallel_llm(
    name="review_parallel",
    fan_in=AgentSpec(name="aggregator", instruction="Merge named reviews into one verdict."),
    fan_out=[
        AgentSpec(name="security", instruction="Review security risks."),
        AgentSpec(name="correctness", instruction="Review functional correctness."),
    ],
    provider="openai",
    model=None,
    request_params=RequestParams(maxTokens=2000, temperature=0.2),
    context=running_app.context,
)
summary = await parallel.generate_str("Review this change.")
```

Direct constructor shape:

```python
parallel = ParallelLLM(
    fan_in_agent=aggregator_agent_or_llm_or_callable,
    fan_out_agents=[agent_or_llm_a, agent_or_llm_b],
    fan_out_functions=[deterministic_check],
    name="review_parallel",
    llm_factory=provider_llm_factory,
    context=running_app.context,
)
```

`fan_in_agent` can be an `Agent`, `AugmentedLLM`, or callable accepting `FanInInput`. Fan-out workers can be agents/LLMs or callables. If a raw `Agent` is used, an `llm_factory` is required.

## Orchestrator

Direct imports:

```python
from mcp_agent.workflows.orchestrator.orchestrator import Orchestrator, OrchestratorOverrides
from mcp_agent.workflows.orchestrator.orchestrator_models import PlanResult
```

Factory:

```python
orchestrator = create_orchestrator(
    available_agents=[
        AgentSpec(name="researcher", instruction="Gather evidence.", server_names=["fetch"]),
        AgentSpec(name="writer", instruction="Synthesize findings."),
    ],
    planner=None,
    synthesizer=None,
    plan_type="full",  # or "iterative"
    provider="openai",
    model=None,
    overrides=OrchestratorOverrides(
        planner_instruction="Create 2-4 concrete steps.",
        synthesizer_instruction="Return Markdown with a concise conclusion.",
    ),
    name="research_orchestrator",
    context=running_app.context,
)
text = await orchestrator.generate_str("Research and summarize the topic.")
plan_result = await orchestrator.execute("Research and summarize the topic.")
```

Constructor shape:

```python
Orchestrator(
    llm_factory=provider_llm_factory,
    name=None,
    planner=None,
    synthesizer=None,
    available_agents=[agent_or_llm],
    plan_type="full",
    overrides=None,
    context=running_app.context,
)
```

Valid `plan_type` values are `"full"` and `"iterative"`. History tracking is not supported by orchestrator workflows; defaults include `use_history=False` and a larger `maxTokens`.

## Deep Orchestrator

Imports:

```python
from mcp_agent.workflows.deep_orchestrator.orchestrator import DeepOrchestrator
from mcp_agent.workflows.deep_orchestrator.config import DeepOrchestratorConfig
```

Factory:

```python
config = DeepOrchestratorConfig.from_simple(
    name="DeepResearch",
    max_iterations=12,
    max_tokens=60_000,
    max_cost=2.00,
    enable_parallel=True,
).with_minimal_context(task_context_budget=12_000)

deep = create_deep_orchestrator(
    available_agents=[AgentSpec(name="researcher", instruction="Extract verifiable facts.")],
    config=config,
    name="DeepResearch",
    provider="openai",
    model=None,
    context=running_app.context,
)
answer = await deep.generate_str("Investigate this complex topic.")
```

Useful config groups:

- `config.execution`: `max_iterations`, `max_replans`, `max_task_retries`, `enable_parallel`, `enable_filesystem`.
- `config.context`: `task_context_budget`, relevance threshold, compression ratio, full-context propagation.
- `config.budget`: `max_tokens`, `max_cost`, `max_time_minutes`, `cost_per_1k_tokens`.
- `config.policy`: consecutive failure limit, verification confidence, budget critical threshold.
- `config.cache`: agent cache size and enable flag.

## Evaluator-Optimizer

Imports:

```python
from mcp_agent.workflows.evaluator_optimizer.evaluator_optimizer import (
    EvaluationResult,
    EvaluatorOptimizerLLM,
    QualityRating,
)
```

Factory:

```python
loop = create_evaluator_optimizer_llm(
    optimizer=AgentSpec(name="writer", instruction="Draft the answer."),
    evaluator="Rate from POOR to EXCELLENT. Require citations and actionable steps.",
    name="checked_writer",
    min_rating=QualityRating.GOOD,
    max_refinements=3,
    provider="openai",
    model=None,
    request_params=RequestParams(temperature=0.2),
    context=running_app.context,
)
text = await loop.generate_str("Write a migration plan.")
```

Constructor shape:

```python
EvaluatorOptimizerLLM(
    optimizer=agent_or_augmented_llm,
    evaluator=string_or_agent_or_augmented_llm,
    name=None,
    min_rating=QualityRating.GOOD,
    max_refinements=3,
    llm_factory=provider_llm_factory,
    context=running_app.context,
)
```

`QualityRating` values are `POOR = 0`, `FAIR = 1`, `GOOD = 2`, and `EXCELLENT = 3`. The loop records `refinement_history` with each response and `EvaluationResult`.

## Swarm

Imports:

```python
from mcp_agent.workflows.swarm.swarm import AgentFunctionResult, DoneAgent, SwarmAgent
from mcp_agent.workflows.swarm.swarm_openai import OpenAISwarm
from mcp_agent.workflows.swarm.swarm_anthropic import AnthropicSwarm
```

Factory:

```python
swarm = create_swarm(
    name="triage",
    instruction="Ask clarifying questions, then hand off with function tools.",
    server_names=[],
    functions=[transfer_to_specialist],
    provider="openai",
    context=running_app.context,
)
```

Direct shape:

```python
def transfer_to_specialist():
    return specialist_agent

def update_case_context():
    return AgentFunctionResult(
        value="Captured case metadata.",
        context_variables={"case_type": "billing"},
        agent=specialist_agent,
    )

triage = SwarmAgent(
    name="triage",
    instruction=lambda ctx: f"Triage with case type {ctx.get('case_type', 'unknown')}.",
    functions=[transfer_to_specialist, update_case_context],
    server_names=[],
    parallel_tool_calls=False,
    context=running_app.context,
)
swarm = OpenAISwarm(agent=triage, context_variables={"case_type": "unknown"})
result = await swarm.generate_str("I need help changing my plan.")
```

A swarm function may return `str`, `dict`, another `Agent`/`SwarmAgent`, or `AgentFunctionResult`. Returning `DoneAgent()` ends the workflow. `swarm.set_agent(...)` switches active agent and recomputes callable instructions from context variables.

## Structured Output

Any `AugmentedLLM`-compatible pattern can expose structured output when the underlying provider supports it:

```python
from pydantic import BaseModel, Field
from mcp_agent.workflows.factory import RequestParams

class ReviewSummary(BaseModel):
    verdict: str = Field(description="approve, revise, or reject")
    risks: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)

summary = await workflow.generate_structured(
    "Review this proposal.",
    response_model=ReviewSummary,
    request_params=RequestParams(strict=True, temperature=0),
)
```

Parallel, orchestrator, evaluator-optimizer, and router workflows each implement `generate_structured`, but note the internal behavior:

- `ParallelLLM.generate_structured` fan-outs first, then asks the fan-in aggregator to produce the requested model.
- `Orchestrator.generate_structured` executes the plan, then asks the synthesizer for the requested model.
- `EvaluatorOptimizerLLM.generate_structured` optimizes text first, then asks the optimizer LLM to convert the final answer into the requested model.
- `LLMRouter.generate_structured` routes to a delegate LLM and forwards the structured request.
