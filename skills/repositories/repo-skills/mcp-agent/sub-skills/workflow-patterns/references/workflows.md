# Workflow Skeletons

These skeletons are adapted from the repository workflow examples into self-contained templates. Replace server names, provider settings, and agent instructions with your app’s needs. All examples assume they run inside an async function.

## Shared App Shape

```python
from mcp_agent.app import MCPApp
from mcp_agent.workflows.factory import AgentSpec, RequestParams

app = MCPApp(name="workflow_app")

async def main():
    async with app.run() as running_app:
        ctx = running_app.context
        # Build workflow here.
```

For basic app, server, and `Agent` setup, use `../core-sdk/SKILL.md`.

## LLM Router Skeleton

Use this when routing to concrete destinations.

```python
from mcp_agent.workflows.factory import AgentSpec, RequestParams, create_router_llm

async with app.run() as running_app:
    router = await create_router_llm(
        name="task_router",
        agents=[
            AgentSpec(
                name="reader",
                instruction="Read and summarize requested source material.",
                server_names=["filesystem"],
            ),
            AgentSpec(
                name="writer",
                instruction="Draft polished user-facing text.",
            ),
        ],
        functions=[lambda request: f"Fallback received: {request}"],
        routing_instruction=(
            "Choose the most specific destination. Prefer reader for file requests, "
            "writer for prose generation, and fallback only for unsupported tasks."
        ),
        provider="openai",
        request_params=RequestParams(temperature=0),
        context=running_app.context,
    )

    choices = await router.route_to_agent("Summarize README.md", top_k=1)
    if not choices or choices[0].confidence != "high":
        raise ValueError("No high-confidence agent route")

    selected = choices[0].result
    async with selected:
        answer = await selected.generate_str("Summarize README.md")
```

When handling mixed destinations from `router.route(...)`, inspect `choice.result` rather than expecting a `choice.category` field. Use `route_to_agent`, `route_to_server`, or `route_to_function` when possible.

## Embedding Router Skeleton

Use this when category descriptions/examples are stable and provider embeddings are installed.

```python
from mcp_agent.workflows.factory import AgentSpec, create_router_embedding

async with app.run() as running_app:
    router = await create_router_embedding(
        provider="openai",  # or "cohere"
        agents=[
            AgentSpec(name="billing", instruction="Handle invoices, plans, and payments."),
            AgentSpec(name="support", instruction="Handle troubleshooting and setup questions."),
        ],
        context=running_app.context,
    )

    results = await router.route_to_agent("Why was my card charged twice?", top_k=2)
    selected_agent = results[0]
```

Provider default embedding models may instantiate API clients. If optional extras or keys are missing, pass a custom `EmbeddingModel` or use LLM routing instead.

## Intent Classifier then Router

Use this when a fixed taxonomy should gate later execution.

```python
from mcp_agent.workflows.factory import (
    AgentSpec,
    RequestParams,
    create_intent_classifier_llm,
    create_router_llm,
)
from mcp_agent.workflows.intent_classifier.intent_classifier_base import Intent

intents = [
    Intent(
        name="file_lookup",
        description="Requests to open, read, or summarize files.",
        examples=["show README", "open pyproject", "summarize this file"],
    ),
    Intent(
        name="general_answer",
        description="Questions that can be answered without tool access.",
        examples=["explain MCP", "what is a router pattern"],
    ),
]

async with app.run() as running_app:
    classifier = await create_intent_classifier_llm(
        intents=intents,
        provider="openai",
        request_params=RequestParams(temperature=0, strict=True),
        context=running_app.context,
    )
    router = await create_router_llm(
        agents=[
            AgentSpec(name="file_agent", instruction="Use filesystem tools for file requests.", server_names=["filesystem"]),
            AgentSpec(name="qa_agent", instruction="Answer conceptual questions."),
        ],
        provider="openai",
        context=running_app.context,
    )

    request = "Can you explain the config file?"
    intent = (await classifier.classify(request, top_k=1))[0]
    if getattr(intent, "confidence", "low") != "high":
        return "I need a clarifying detail before continuing."

    route = await router.route_to_agent(f"[intent={intent.intent}] {request}", top_k=1)
```

## Parallel Fan-Out/Fan-In Skeleton

Use this for independent reviewers, voters, or map-reduce-style analysis.

```python
from mcp_agent.workflows.factory import AgentSpec, RequestParams, create_parallel_llm
from mcp_agent.workflows.parallel.fan_in import FanInInput


def deterministic_summary(messages: FanInInput) -> str:
    sections = []
    for source, outputs in messages.items():
        text = "\n".join(str(item) for item in outputs)
        sections.append(f"## {source}\n{text}")
    return "\n\n".join(sections)

async with app.run() as running_app:
    parallel = create_parallel_llm(
        name="review_parallel",
        fan_in=AgentSpec(
            name="aggregator",
            instruction="Merge named reviewer outputs. Flag disagreements and give a final verdict.",
        ),
        fan_out=[
            AgentSpec(name="security", instruction="Find security risks."),
            AgentSpec(name="correctness", instruction="Find correctness issues."),
            AgentSpec(name="maintainability", instruction="Find maintainability risks."),
        ],
        provider="openai",
        request_params=RequestParams(maxTokens=2000, temperature=0.2),
        context=running_app.context,
    )
    report = await parallel.generate_str("Review this patch summary.")

    deterministic_parallel = create_parallel_llm(
        fan_in=deterministic_summary,
        fan_out=[AgentSpec(name="qa", instruction="Answer with concrete findings.")],
        context=running_app.context,
    )
```

Fan-in receives outputs keyed by worker/function name. Do not assume branch order or that all branches agree.

## Orchestrator Skeleton

Use this when the workflow must plan steps and delegate dynamically.

```python
from mcp_agent.workflows.factory import AgentSpec, OrchestratorOverrides, create_orchestrator

async with app.run() as running_app:
    orchestrator = create_orchestrator(
        available_agents=[
            AgentSpec(name="researcher", instruction="Gather evidence from available sources.", server_names=["fetch"]),
            AgentSpec(name="analyst", instruction="Analyze evidence and identify trade-offs."),
            AgentSpec(name="writer", instruction="Produce concise Markdown output."),
        ],
        plan_type="iterative",  # or "full"
        overrides=OrchestratorOverrides(
            planner_instruction="Create short, verifiable steps and assign the best worker.",
            synthesizer_instruction="Return a final answer with decisions, evidence, and open risks.",
        ),
        provider="openai",
        context=running_app.context,
    )

    answer = await orchestrator.generate_str("Research the topic and draft a recommendation.")
    plan_result = await orchestrator.execute("Research the topic and draft a recommendation.")
```

Use `execute(...)` when you need the `PlanResult` for UI, audit, or tests.

## Deep Orchestrator Skeleton

Use this for longer research loops with policy and budget controls.

```python
from mcp_agent.workflows.factory import AgentSpec, create_deep_orchestrator
from mcp_agent.workflows.deep_orchestrator.config import DeepOrchestratorConfig

async with app.run() as running_app:
    config = DeepOrchestratorConfig.from_simple(
        name="deep_research",
        max_iterations=10,
        max_tokens=50_000,
        max_cost=1.00,
        enable_parallel=True,
    ).with_strict_budget(max_tokens=40_000, max_cost=0.75, max_time_minutes=10)

    deep = create_deep_orchestrator(
        available_agents=[
            AgentSpec(name="researcher", instruction="Find verifiable facts."),
            AgentSpec(name="writer", instruction="Synthesize accumulated knowledge."),
        ],
        config=config,
        provider="openai",
        context=running_app.context,
    )

    result = await deep.generate_str("Investigate this long-horizon research question.")
```

Start with `Orchestrator` unless you need memory, replanning, policy, and budget behavior.

## Evaluator-Optimizer Skeleton

Use this when quality can be judged by a clear rubric.

```python
from mcp_agent.workflows.factory import AgentSpec, RequestParams, create_evaluator_optimizer_llm
from mcp_agent.workflows.evaluator_optimizer.evaluator_optimizer import QualityRating

async with app.run() as running_app:
    checked_writer = create_evaluator_optimizer_llm(
        optimizer=AgentSpec(name="writer", instruction="Draft a complete answer."),
        evaluator=(
            "Evaluate against: factual accuracy, citations when needed, concise structure, "
            "and no unsupported claims. Mark needs_improvement true if any criterion fails."
        ),
        min_rating=QualityRating.GOOD,
        max_refinements=2,
        provider="openai",
        request_params=RequestParams(temperature=0.2),
        context=running_app.context,
    )

    answer = await checked_writer.generate_str("Draft a release note.")
    history = checked_writer.refinement_history
```

If `QualityRating.EXCELLENT` is required, expect more iterations and token spend.

## Swarm Skeleton

Use this when tool calls should transfer control between conversation agents.

```python
from mcp_agent.workflows.swarm.swarm import AgentFunctionResult, DoneAgent, SwarmAgent
from mcp_agent.workflows.swarm.swarm_openai import OpenAISwarm

billing_agent = None
support_agent = None


def transfer_to_billing():
    return billing_agent


def transfer_to_support():
    return support_agent


def resolve_case():
    return DoneAgent()


def update_context():
    return AgentFunctionResult(
        value="Updated case context.",
        context_variables={"case_status": "triaged"},
    )

async with app.run() as running_app:
    billing_agent = SwarmAgent(
        name="billing",
        instruction="Handle billing issues. Resolve with resolve_case when done.",
        functions=[resolve_case],
        context=running_app.context,
    )
    support_agent = SwarmAgent(
        name="support",
        instruction="Handle technical support issues. Resolve with resolve_case when done.",
        functions=[resolve_case],
        context=running_app.context,
    )
    triage = SwarmAgent(
        name="triage",
        instruction=lambda ctx: f"Triage the customer. Current status: {ctx.get('case_status', 'new')}",
        functions=[transfer_to_billing, transfer_to_support, update_context],
        context=running_app.context,
    )

    swarm = OpenAISwarm(agent=triage, context_variables={"case_status": "new"})
    response = await swarm.generate_str("I was charged twice and need help.")
```

Use `AnthropicSwarm` instead of `OpenAISwarm` for Anthropic provider. Swarm transfer functions must return an agent, `AgentFunctionResult`, plain string/dict, or `DoneAgent()`.

## Structured Output Skeleton

Use this for machine-readable outputs from any compatible pattern.

```python
from pydantic import BaseModel, Field
from mcp_agent.workflows.factory import RequestParams

class Decision(BaseModel):
    action: str = Field(description="next action to take")
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)

result = await workflow.generate_structured(
    "Decide the next action for this support request.",
    response_model=Decision,
    request_params=RequestParams(strict=True, temperature=0),
)
```

If provider extras are not installed or strict structured output is unavailable, keep the schema model but catch validation/provider errors and fall back to text plus deterministic validation.

## Composition Skeleton: Router to Parallel to Evaluator

```python
from mcp_agent.workflows.factory import (
    AgentSpec,
    create_evaluator_optimizer_llm,
    create_parallel_llm,
    create_router_llm,
)
from mcp_agent.workflows.evaluator_optimizer.evaluator_optimizer import QualityRating

async with app.run() as running_app:
    parallel_review = create_parallel_llm(
        fan_in=AgentSpec(name="review_aggregator", instruction="Merge reviews into a final recommendation."),
        fan_out=[
            AgentSpec(name="risk", instruction="Find risks."),
            AgentSpec(name="value", instruction="Find user value."),
        ],
        context=running_app.context,
    )
    reviewed = create_evaluator_optimizer_llm(
        optimizer=parallel_review,
        evaluator="Require a clear recommendation, risks, and actionable next steps.",
        min_rating=QualityRating.GOOD,
        max_refinements=2,
        context=running_app.context,
    )
    router = await create_router_llm(
        agents=[
            AgentSpec(name="simple", instruction="Answer simple questions directly."),
            reviewed,
        ],
        context=running_app.context,
    )
```

When composing, ensure names remain unique and cost grows with every nested branch.
