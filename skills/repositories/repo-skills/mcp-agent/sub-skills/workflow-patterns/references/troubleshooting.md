# Workflow Troubleshooting

Use this checklist when an mcp-agent workflow fails to import, initialize, route, classify, aggregate, refine, or validate structured output.

## Import and Class Name Errors

### Symptom

`ImportError`, `AttributeError`, or code refers to `RouterLLM`.

### Fix

- Use `LLMRouter`, not `RouterLLM`.
- Prefer factory helpers from `mcp_agent.workflows.factory`.
- Verify direct imports with `scripts/check_workflow_imports.py`.

Correct imports:

```python
from mcp_agent.workflows.router.router_llm import LLMRouter
from mcp_agent.workflows.router.router_embedding import EmbeddingRouter
from mcp_agent.workflows.parallel.parallel_llm import ParallelLLM
from mcp_agent.workflows.orchestrator.orchestrator import Orchestrator, OrchestratorOverrides
from mcp_agent.workflows.evaluator_optimizer.evaluator_optimizer import EvaluatorOptimizerLLM, QualityRating
from mcp_agent.workflows.intent_classifier.intent_classifier_base import Intent
from mcp_agent.workflows.intent_classifier.intent_classifier_llm import LLMIntentClassifier
from mcp_agent.workflows.swarm.swarm import SwarmAgent, DoneAgent, AgentFunctionResult
```

## Missing Provider Extras or API Keys

### Symptom

Provider imports fail, embedding model constructors fail, or runtime complains about missing API keys.

### Fix

- Importing workflow classes is not enough to prove provider clients can run.
- OpenAI and Cohere embedding model defaults instantiate provider clients and read configured API keys.
- LLM router/classifier provider wrappers may instantiate `OpenAIAugmentedLLM` or `AnthropicAugmentedLLM`.
- Use the import checker without provider client instantiation first, then opt in to provider checks only when the environment is configured.
- In a source checkout without installed dependencies, run `python scripts/check_workflow_imports.py --source-only` to validate names by parsing source files.
- If embeddings are unavailable, use `create_router_llm(...)` or `create_intent_classifier_llm(...)` instead of embedding variants.

## `llm_factory` Required

### Symptom

`ValueError: llm_factory must be provided` or fan-out/fan-in fails when using raw `Agent` objects.

### Cause

Direct classes need a way to attach an `AugmentedLLM` to raw agents.

### Fix

- Use factory helpers such as `create_parallel_llm(...)`, `create_router_llm(...)`, or `create_orchestrator(...)`; they create provider factories for you.
- If using direct constructors, pass `llm_factory`, for example `lambda agent, **kw: OpenAIAugmentedLLM(agent=agent, instruction=kw.get("instruction"), context=ctx)`.
- Passing an existing `AugmentedLLM` avoids the need for a factory for that object.

## Router Category Ambiguity

### Symptom

Router returns no choices, low confidence, or an unexpected destination.

### Fix

- Make agent instructions and function docstrings distinct. Router category descriptions come from agent instructions and function schemas.
- Add examples or constraints in `routing_instruction`.
- Use `route_to_agent`, `route_to_server`, or `route_to_function` if the destination type is known.
- Use `top_k > 1` and compare `confidence`/`reasoning` for review flows.
- Gate automation on `confidence == "high"`; ask a clarifying question otherwise.
- Do not expect `LLMRouterResult.category` to exist. Use `choice.result` or destination-specific methods.

## Server Routing Fails

### Symptom

Router initialization fails when `server_names` are provided.

### Cause

Server categories require a server registry in context.

### Fix

- Build routers inside `async with app.run() as running_app:`.
- Pass `context=running_app.context`.
- Confirm the named MCP server is configured before routing to it.
- If you only need agents or functions, omit `server_names`.

## Embedding Router or Classifier Scores Look Wrong

### Symptom

Top embedding match is semantically weak or unstable.

### Fix

- Improve category/intent descriptions and examples; embedding matching only sees text representation.
- Prefer embedding intent classifier for fixed taxonomies and embedding router for concrete destinations.
- Add threshold logic on `p_score`; do not blindly execute a weak match.
- Rebuild the router/classifier after changing categories because embeddings are precomputed during initialization.
- Use an LLM classifier/router when distinctions require reasoning over context rather than semantic similarity.

## Unsafe Parallel Fan-In Assumptions

### Symptom

Fan-in selects a bad answer, branch disagreement is hidden, or deterministic aggregator crashes.

### Cause

`ParallelLLM` fan-out returns a mapping keyed by worker/function name. Workers run independently and may disagree or fail.

### Fix

- Aggregate by source name, not by list position.
- Ask the fan-in agent to call out disagreements and missing branches.
- For deterministic fan-in functions, accept all `FanInInput` shapes you use and convert outputs with `str(...)` defensively.
- Keep fan-out workers independent; use an orchestrator for dependencies.
- Cap concurrency globally through executor settings when external tools or APIs cannot handle many calls.

## Evaluator Never Reaches `min_rating`

### Symptom

Evaluator-optimizer runs to `max_refinements` and still returns a weak answer.

### Fix

- Make evaluator criteria concrete and compatible with `EvaluationResult` fields.
- Set `min_rating=QualityRating.GOOD` before requiring `EXCELLENT`.
- Keep `max_refinements` low and inspect `refinement_history`.
- Ensure evaluator feedback includes actionable `focus_areas`.
- If the optimizer lacks required tools or context, wrapping it in an evaluator loop will not fix capability gaps.
- For policy gates, treat failure to reach threshold as a review/escalation signal, not success.

## Orchestrator Planning Problems

### Symptom

Planner chooses wrong workers, loops too long, or output is too large.

### Fix

- Give every available agent a unique name and explicit instruction.
- Use `plan_type="full"` for predictable tasks and `"iterative"` for exploratory tasks.
- Override planner/synthesizer instructions with `OrchestratorOverrides`.
- Lower `RequestParams.max_iterations` for bounded runs.
- Use `execute(...)` and inspect `PlanResult.step_results` to debug worker choices.
- Remember orchestrator history is disabled; context is carried through plan state, not normal chat history.

## Deep Orchestrator Budget or Memory Issues

### Symptom

Long run stops early, replans repeatedly, or consumes too much context.

### Fix

- Configure `DeepOrchestratorConfig` budgets before running.
- Use `.with_strict_budget(...)` and `.with_minimal_context(...)` for constrained environments.
- Check `config.execution.max_iterations`, `max_replans`, and `max_task_retries`.
- Use normal `Orchestrator` if you do not need knowledge extraction, policy, and budget management.

## Swarm Handoff Does Not Switch Agents

### Symptom

A swarm tool returns text but active agent does not change.

### Cause

Only specific return types trigger handoff or context updates.

### Fix

- Return an `Agent`/`SwarmAgent` to transfer directly.
- Return `AgentFunctionResult(agent=next_agent, context_variables={...})` to transfer and update context.
- Return `DoneAgent()` to end the workflow.
- Ensure transfer functions are included in the active `SwarmAgent(functions=[...])`.
- If instructions are callables, they are recomputed from `context_variables` when `set_agent(...)` runs.

## Structured Output Schema Mismatch

### Symptom

`generate_structured` fails validation, returns malformed JSON, or provider rejects strict mode.

### Fix

- Keep Pydantic models small and explicit.
- Use `RequestParams(strict=True, temperature=0)` when supported.
- Provide `Field(description=...)` on ambiguous fields.
- Avoid unions and deeply nested schemas in early drafts.
- For `ParallelLLM`, remember the fan-in aggregator produces the final structured model.
- For `Orchestrator`, structured output happens after plan execution and synthesis.
- For `EvaluatorOptimizerLLM`, final text is generated first, then converted to the requested model.
- If provider extras are missing, catch the provider/import error and fall back to text plus deterministic validation.

## Token and Cost Surprises

### Symptom

Nested workflow costs exceed expectations.

### Fix

- Estimate calls before running: parallel branches + fan-in, evaluator iterations, planner loops, and synthesis all add calls.
- Use `RequestParams(maxTokens=...)` to cap long generations.
- Use `await workflow.get_token_node()` after runs to inspect branches.
- Prefer embedding or deterministic functions for cheap classification when appropriate.
- Cache reusable routers/classifiers/workflows at app startup when safe.

## Pre-Run Validation Checklist

1. `python scripts/check_workflow_imports.py` passes in an installed target environment, or `python scripts/check_workflow_imports.py --source-only` passes in a dependency-light source checkout.
2. `python scripts/pattern_skeletons.py --help` and `--list` work.
3. Provider-specific smoke tests are skipped unless optional extras and API keys are configured.
4. Router/classifier ambiguous cases have a fallback path.
5. Parallel fan-in handles missing, noisy, or disagreeing branches.
6. Evaluator loops have bounded `max_refinements`.
7. Structured output has a validation fallback.
8. Long-horizon orchestrations have explicit token/cost/time budgets.
