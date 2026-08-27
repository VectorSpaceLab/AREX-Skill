# Pattern Selection for mcp-agent Workflows

Choose the smallest workflow that gives the control you need. All major patterns behave like `AugmentedLLM` objects, so they can be nested, wrapped, exposed as tools, or passed as workers to other patterns.

## Decision Matrix

| Need | Choose | Why | Avoid when |
| --- | --- | --- | --- |
| Dispatch one request to one or more capable destinations | `create_router_llm(...)` / `LLMRouter` | Uses an LLM over server, agent, and callable descriptions; returns ranked `LLMRouterResult` with confidence and reasoning | You only need fixed labels and no destination execution |
| Deterministic semantic dispatch over stable categories | `create_router_embedding(...)` / `EmbeddingRouter` | Precomputes category embeddings and ranks by similarity score | Provider embeddings or API keys are unavailable |
| Classify user language into fixed intents | `create_intent_classifier_llm(...)` / `LLMIntentClassifier` | Returns intent, confidence, reasoning, `p_score`, and extracted entities | You need to execute a destination directly; use a router after classification |
| Low-latency fixed intent matching | `create_intent_classifier_embedding(...)` | Ranks intents by embedding similarity without a classifier LLM | Intent examples are sparse or ambiguous |
| Multiple independent reviewers or workers should see the same prompt | `create_parallel_llm(...)` / `ParallelLLM` | Fan-out workers run concurrently; fan-in aggregates named outputs | Workers depend on each other’s intermediate results |
| A complex objective needs dynamic planning and worker assignment | `create_orchestrator(...)` / `Orchestrator` | Planner builds sequential steps with parallel tasks and synthesizes results | The request is a simple dispatch or fixed checklist |
| Long-horizon research needs budgets, knowledge memory, and replanning | `create_deep_orchestrator(...)` / `DeepOrchestrator` | Adds queue, knowledge extraction, policy, budget, and agent caching | You only need a short, predictable plan |
| Output should improve until a rubric passes | `create_evaluator_optimizer_llm(...)` / `EvaluatorOptimizerLLM` | Evaluator returns `EvaluationResult` and optimizer refines until `min_rating` or cap | Rubric is vague or no bounded iteration budget exists |
| A conversation should hand off between specialized agents | `create_swarm(...)`, `OpenAISwarm`, or `AnthropicSwarm` | Tool-call results can switch the active `SwarmAgent` and update context variables | You need planner-managed task decomposition rather than conversational handoff |
| A custom map-reduce/planner composition is needed | Mix factory helpers | Patterns are composable `AugmentedLLM`s and callables | A built-in helper already fits directly |

## Router vs Intent Classifier vs Orchestrator

Use this rule of thumb for ambiguous multi-agent tasks:

- Pick an **intent classifier** when the first question is "what kind of request is this?" and the answer should be a fixed label such as `refund`, `technical_support`, or `file_lookup`.
- Pick a **router** when the first question is "which destination should handle this?" and candidates are concrete agents, MCP servers, or Python functions.
- Pick an **orchestrator** when the first question is "what steps are needed?" and the system must discover a plan before selecting workers.
- Combine them when useful: classify coarse intent, route within that intent, then send complex destinations to an orchestrator.

Example composition:

```python
intent = (await classifier.classify(request, top_k=1))[0]
if getattr(intent, "confidence", "medium") != "high":
    return "I need a clarifying detail before automating this."

choices = await router.route(f"[intent={intent.intent}] {request}", top_k=1)
if not choices:
    return "No confident destination matched."

routed = choices[0].result
```

## Parallel vs Orchestrator

- Choose **parallel** when every worker can answer the same prompt independently and the fan-in step can merge results.
- Choose **orchestrator** when the task requires sequencing, dependencies, planner-created subtasks, or different prompts per worker.
- Combine them by using a `ParallelLLM` as one orchestrator worker for a step that benefits from multiple reviewers.

## Evaluator-Optimizer Placement

Evaluator-optimizer loops are wrappers. Good placements:

- Around a writer agent for policy, style, or citation review.
- Around a `ParallelLLM` to refine the aggregated output, not every branch.
- Around the final synthesis of an orchestrator when the rubric is global.

Keep `max_refinements` small. Each refinement adds at least one evaluator call and often another optimizer call.

## Deep Orchestrator Criteria

Use `DeepOrchestrator` only when at least two of these are true:

- The run may require many iterations or replanning.
- You need knowledge extraction and retrieval across steps.
- Budget/cost/time policy should influence continuation.
- Agents may be dynamically designed or cached.
- Progress dashboards or reviewable queue state matter.

Otherwise, start with `Orchestrator`.

## Structured Output Choice

Use structured output when downstream code must rely on fields, not prose. Define a Pydantic model, pass it as `response_model`, and prefer `RequestParams(strict=True)` for providers that support schema strictness.

Good structured-output targets:

- Router or classifier post-processing summaries.
- Aggregated parallel findings with `verdict`, `issues`, and `confidence` fields.
- Orchestrator synthesis with `status`, `steps`, and `recommendations`.

Avoid structured output when provider extras are not installed or the schema is too complex for the selected model. In that case, generate text first and validate or parse in a deterministic second step.

## Token and Cost Heuristics

- Router LLM: one classifier call, plus optional downstream execution.
- Embedding router/classifier: embedding calls for categories/intents during initialization and one embedding call per request.
- Parallel: roughly `fan_out_count + fan_in` calls per request.
- Orchestrator: planner calls plus worker calls per task plus synthesizer call; iterative planning can multiply this.
- Evaluator-optimizer: initial optimizer call plus evaluator calls and refinement optimizer calls until threshold or cap.
- Deep orchestrator: planner, verifier, task execution, knowledge extraction, and synthesis loops; set explicit budgets.

## Validation Before Shipping

- Verify imports with this sub-skill’s `scripts/check_workflow_imports.py`.
- Print and adapt skeletons with `scripts/pattern_skeletons.py --list` and `--pattern <name>`.
- For routers/classifiers, test low-confidence or ambiguous prompts.
- For parallel workflows, test one slow or noisy branch and ensure fan-in handles disagreement.
- For structured output, test schema validation failures and fallback behavior.
