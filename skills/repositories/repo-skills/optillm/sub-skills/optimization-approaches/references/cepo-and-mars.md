# CePO and MARS

Read this for OptiLLM's advanced, expensive reasoning approaches.

## CePO: Cerebras Planning and Optimization

CePO combines Best-of-N, chain-of-thought, self-reflection, self-improvement, and prompting techniques. A typical completion cycle is:

1. Generate a detailed plan and confidence by step.
2. Generate an initial solution from the plan.
3. Repeat planning/solution generation for multiple proposals.
4. Refine plans by comparing inconsistencies.
5. Produce a final answer from the refined plan.

### Important config fields

CePO config files define fields such as:

- `bestofn_n`, `bestofn_temperature`, `bestofn_max_tokens`, `bestofn_rating_type`
- `planning_n`, `planning_m`
- `planning_temperature_step1`, `planning_temperature_step2`, `planning_temperature_direct_resp`, `planning_temperature_step3`, `planning_temperature_step4`
- `planning_max_tokens_step1`, `planning_max_tokens_step2`, `planning_max_tokens_direct_resp`, `planning_max_tokens_step3`, `planning_max_tokens_step4`
- `use_plan_diversity`, `rating_model`, `use_reasoning`, `use_reasoning_fallback`, `num_of_retries`, `print_output`

Use a task-appropriate config file and check whether token limits match the backend. Qwen/GPT-OSS configs use larger token budgets than the default config.

### When to use CePO

- Math or coding tasks where planning quality matters.
- Situations where multiple solution proposals and a refined final plan are worth the latency.
- Cerebras or fast backends where multi-step inference is affordable.

### CePO cautions

- It can be expensive: planning counts and token limits multiply.
- A config path mismatch can silently use defaults or fail during startup.
- Majority rating expects extractable final answers; proof tasks may need different answer handling.

## MARS: Multi-Agent Reasoning System

MARS uses multiple agents, diverse temperatures, verification, iterative improvement, optional aggregation, and a strategy network. It is designed for difficult mathematical and coding tasks.

### Default behavior

Default MARS configuration includes:

- `num_agents`: 3
- `max_iterations`: 5
- `verification_passes_required`: 2
- `consensus_threshold`: 2
- `max_tokens`: 64000
- `use_reasoning_api`: true
- `enable_aggregation`: true
- `enable_strategy_network`: true
- `use_thinking_tags`: true
- `answer_extraction_mode`: `auto`

MARS automatically uses a lightweight configuration when `max_tokens <= 4000`, reducing agents/iterations and disabling expensive aggregation/strategy-network features.

### When to use MARS

- AIME/IMO-like math problems.
- Competitive programming or code generation when multiple independent solution paths help.
- Cases where verification and consensus are more important than latency.

### Thinking tags and answer extraction

MARS can wrap reasoning in `<think>` tags and extract clean answers. This helps numerical/code tasks but can hide proof details from evaluators if the final output strips reasoning. For proof-heavy tasks, consider disabling thinking tags or answer extraction so the proof remains visible.

### Request config knobs

MARS reads request configuration for agent counts, iterations, token limits, aggregation, strategy network, thinking tags, and answer extraction. Keep token budgets explicit to avoid runaway costs.

## Choosing CePO versus MARS

| Situation | Prefer |
| --- | --- |
| Need structured planning and refinement | CePO |
| Need parallel independent agents and verification | MARS |
| Fast backend and high accuracy target | CePO or MARS |
| Proof visibility matters | MARS with thinking/answer extraction adjusted, or CePO with final output inspection |
| Tight latency/cost | Neither; start with `re2`, `cot_reflection`, or `plansearch` |

## Safe validation

Before a real benchmark:

1. Parse the approach string offline with `scripts/approach_matrix.py`.
2. Run mock-client approach tests if editing the repo.
3. Set small token budgets and agent/planning counts for a smoke request.
4. Check provider support for max token fields and reasoning API features.
5. Only then run benchmark-scale scripts with explicit datasets, model, API keys, and output paths.
