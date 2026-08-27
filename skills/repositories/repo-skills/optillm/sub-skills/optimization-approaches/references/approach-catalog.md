# Approach Catalog

Read this to choose OptiLLM core approaches and understand verified signatures.

## Slugs and task fit

| Slug | Best fit | Cost/latency notes |
| --- | --- | --- |
| `none` | Direct provider pass-through | Cheapest; cannot be combined with other approaches. |
| `re2` | Rereading/simple reasoning boost | Lightweight; good when provider has limited `n` support. |
| `cot_reflection` | Chain-of-thought plus reflection | Multiple prompt phases; can return full reasoning when configured. |
| `leap` | Few-shot principle extraction and application | Useful when prompt contains examples; extra calls. |
| `plansearch` | Planning over candidate approaches | Good for coding/problem solving; cost grows with `n`. |
| `rto` | Round-trip optimization, especially code-like tasks | Requires response transformation and comparison. |
| `self_consistency` | Generate/cluster/aggregate multiple answers | Higher cost; needs robust provider responses. |
| `bon` | Best-of-N sampling and selection | Requires multiple candidate generations. |
| `moa` | Mixture of agents/critique synthesis | Higher quality for difficult tasks; multiple calls. |
| `mcts` | Monte Carlo tree search for chat decisions | Tune simulations/depth/exploration. |
| `rstar` | R* style search | Async search; tune rollouts/depth. |
| `z3` | Logical/math solving with generated symbolic code | Needs `z3-solver` and `sympy`; verify generated code safety. |
| `pvg` | Prover-verifier game | Multiple solution/verifier rounds. |
| `cepo` | Cerebras Planning and Optimization | Strong math/code planning; config-driven and multi-step. |
| `mars` | Multi-Agent Reasoning System | Strong competition math/code; expensive but configurable. |

## Verified callable signatures

```python
chat_with_mcts(system_prompt, initial_query, client, model, num_simulations=2, exploration_weight=0.2, simulation_depth=1, request_config=None, request_id=None)
best_of_n_sampling(system_prompt, initial_query, client, model, n=3, request_config=None, request_id=None)
mixture_of_agents(system_prompt, initial_query, client, model, request_config=None, request_id=None)
round_trip_optimization(system_prompt, initial_query, client, model, request_config=None, request_id=None)
advanced_self_consistency_approach(system_prompt, initial_query, client, model, request_config=None, request_id=None)
inference_time_pv_game(system_prompt, initial_query, client, model, num_rounds=2, num_solutions=3, request_config=None, request_id=None)
cot_reflection(system_prompt, initial_query, client, model, return_full_response=False, request_config=None, request_id=None)
plansearch(system_prompt, initial_query, client, model, n=1, request_config=None)
leap(system_prompt, initial_query, client, model, request_config=None, request_id=None)
re2_approach(system_prompt, initial_query, client, model, n=1, request_config=None, request_id=None)
cepo(system_prompt, initial_query, client, model, cepo_config, request_id=None)
multi_agent_reasoning_system(system_prompt, initial_query, client, model, request_config=None, request_id=None)
```

The server dispatches these through `execute_single_approach`, so request-level config may be used even when a function signature has defaults.

## Server-level default knobs

| Knob | Default | Applies to |
| --- | --- | --- |
| `mcts_simulations` | `2` | `mcts` |
| `mcts_exploration` | `0.2` | `mcts` |
| `mcts_depth` | `1` | `mcts` |
| `best_of_n` | `3` | `bon` |
| `n` | `1` | final repeated executions, `re2`, `plansearch` |
| `rstar_max_depth` | `3` | `rstar` |
| `rstar_num_rollouts` | `5` | `rstar` |
| `rstar_c` | `1.4` | `rstar` |
| `return_full_response` | false | `cot_reflection` |

MCTS parameters are request scoped in current code; do not rely on mutating global `server_config` during concurrent requests.

## Provider compatibility

When an upstream endpoint cannot return multiple choices from one request, prefer approaches that perform their own sequential calls or do not need `n`. The README specifically warns that Anthropic, llama.cpp-server, and Ollama may limit approaches relying on multiple responses. For those providers, consider `cot_reflection`, `leap`, `plansearch`, `rstar`, `rto`, `self_consistency`, `re2`, or `z3` first.

## Choosing by task

- Arithmetic or brittle short reasoning: start with `re2` or `cot_reflection`.
- Coding problem: try `plansearch`, `rto`, `moa`, `mars` lightweight config, or `cepo` depending on budget.
- Hard math/proof: `mars` or `cepo`; decide whether thinking tags should be visible to graders.
- Majority-style answer extraction: `self_consistency`, `bon`, or `pvg`.
- Symbolic logic/algebra: `z3`, but inspect generated solver code and constraints.
- Accuracy over latency: `moa`, `cepo`, or `mars`.
- Latency/cost constrained: `re2`, `cot_reflection`, or direct `none`.
