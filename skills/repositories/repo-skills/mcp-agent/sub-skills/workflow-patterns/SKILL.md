---
name: workflow-patterns
description: "Choose and implement mcp-agent workflow patterns including
  routers, intent classifiers, parallel fan-out/fan-in, orchestrators,
  evaluators, swarms, and structured outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# mcp-agent Workflow Patterns

Use this sub-skill when a task asks you to choose, compose, or implement an mcp-agent workflow pattern beyond basic `Agent`/`AugmentedLLM` setup. It covers routers, embedding routers, intent classifiers, parallel map-reduce/fan-out/fan-in, orchestrator/deep orchestrator flows, evaluator-optimizer loops, swarm handoffs, planner-style compositions, and structured outputs.

For basic `MCPApp`, `Agent`, server connections, and LLM setup, use the sibling `../core-sdk/SKILL.md`. For Temporal or durable execution semantics, use `../durable-execution/SKILL.md`. This sub-skill focuses on in-process pattern selection and code structure.

## Fast Pattern Choice

- Use `LLMRouter` or `create_router_llm(...)` when a request must be dispatched to the best agent, MCP server, or callable based on candidate descriptions and reasoning.
- Use `EmbeddingRouter` or `create_router_embedding(...)` when categories are stable and semantic-similarity scoring is preferable to another LLM call.
- Use `LLMIntentClassifier` or embedding intent classifiers when you need a fixed intent taxonomy, confidence, and optional extracted entities before routing.
- Use `ParallelLLM` or `create_parallel_llm(...)` when independent specialists can process the same input concurrently and a fan-in step can aggregate their outputs.
- Use `Orchestrator` or `create_orchestrator(...)` when the system must plan sequential steps and delegate tasks to workers dynamically.
- Use `DeepOrchestrator` or `create_deep_orchestrator(...)` for long-horizon research with budgets, memory, policy-driven replanning, and knowledge extraction.
- Use `EvaluatorOptimizerLLM` or `create_evaluator_optimizer_llm(...)` when a clear quality rubric can drive bounded refinement.
- Use `SwarmAgent` plus `OpenAISwarm`, `AnthropicSwarm`, or `create_swarm(...)` when a conversation should hand off between agents while preserving context variables.

## Implementation Checklist

1. Start inside `async with app.run() as running_app:` and pass `context=running_app.context` to factory helpers so server registry, executor, secrets, tracing, and token tracking are shared.
2. Model specialists as `AgentSpec`, `Agent`, existing `AugmentedLLM`, or deterministic callables depending on the helper. Keep agent names unique and instructions capability-specific.
3. Prefer factory helpers from `mcp_agent.workflows.factory` for ordinary application code; drop to provider-specific classes only when you need direct constructor control.
4. For routers, use `LLMRouter`, not `RouterLLM`. Prefer `route_to_agent`, `route_to_server`, or `route_to_function` when the destination type is known.
5. For embedding routers/classifiers, confirm the optional provider package and API key are configured before instantiating provider default models.
6. For parallel workflows, make every fan-out worker independent; aggregate by source name and avoid assuming the first response is the winner.
7. For evaluator loops, pass an explicit `QualityRating` threshold and a small `max_refinements` cap.
8. For structured output, define Pydantic response models and call `generate_structured(..., response_model=YourModel, request_params=RequestParams(strict=True))` where the provider supports strict mode.
9. Inspect token costs with `await workflow.get_token_node()` after nested runs when budget matters.
10. Keep reusable code in your application, not in ad-hoc notebooks; use `scripts/pattern_skeletons.py` from this skill to print safe starting templates.

## Reference Map

- Pattern selection guide: `references/pattern-selection.md`
- Current API and constructors: `references/api-reference.md`
- Reusable workflow skeletons: `references/workflows.md`
- Troubleshooting and validation: `references/troubleshooting.md`
- Import sanity checker: `scripts/check_workflow_imports.py`
- Skeleton printer: `scripts/pattern_skeletons.py`

## Safety Notes

- Provider examples may require optional extras and configured API keys. Import checks should not instantiate network clients unless you explicitly opt in.
- Parallel and orchestrator patterns multiply LLM calls. Estimate worst-case calls before enabling high `top_k`, many fan-out agents, or high refinement counts.
- Router and intent classifier confidence should gate irreversible actions. Escalate or ask a clarifying question when top candidates are close or low-confidence.
- Do not use workflow patterns to expose MCP servers or cloud/CLI operations; use the sibling skills for those areas.
