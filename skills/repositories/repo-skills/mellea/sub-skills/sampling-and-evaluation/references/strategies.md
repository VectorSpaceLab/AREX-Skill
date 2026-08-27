# Strategy selection and operating budgets

Sampling is an inference-time policy, not a proof that a model is correct.
Choose the smallest policy that addresses the observed failure and keep the
policy visible in benchmark metadata.

## Decision table

| Symptom or objective | Strategy | Context requirement | Selection after exhaustion | Cost and reproducibility |
|---|---|---|---|---|
| Occasional stochastic failure; prompt is already good | `RejectionSamplingStrategy` | Any supported context | index `0` | Up to `loop_budget`; same prompt each retry |
| Failure reason should guide the next attempt | `RepairTemplateStrategy` | An `Instruction` gets a repaired copy | index `0` | Up to `loop_budget`; repair text changes prompt |
| Repair should be a new chat turn | `MultiTurnStrategy` | `ChatContext` | last attempt | Up to `loop_budget`; context grows |
| Fast model should handle easy cases, slow model hard cases | `SOFAISamplingStrategy` | `ChatContext` | S2 attempt on final failure | Up to S1 budget plus one S2 generation; two model costs |
| Repeated math answers should converge | `MajorityVotingStrategyForMath` | Backend/context | MBRD selected candidate | `number_of_samples` independent runs and pairwise scoring |
| Free-text consensus is useful | `MBRDRougeLStrategy` | Backend/context | Highest aggregate Rouge-L | Text similarity, not factual correctness |
| Model has explicit think delimiters | `BudgetForcingSamplingStrategy` | Ollama backend | Rejection fallback | Counts completion usage; no tool calls/batching |

The package-level sampling exports include the base strategies, presets, and
`MajorityVotingStrategyForMath`/`MBRDRougeLStrategy`; the latter two are
implemented in a submodule and may require their optional comparison packages.
Budget forcing is imported from its submodule.

## Cost model

For one base action, use this conservative request estimate:

```text
base_requests <= loop_budget * concurrency_budget
majority_requests <= number_of_samples * loop_budget
SOFAI_requests <= loop_budget + 1
```

Each failed requirement can also cause validation work. An LLM-as-a-judge
requirement is another model call per attempt; a separate SOFAI judge can add
more calls. Token caps bound output length but do not bound provider retries,
connection retries, or external evaluator latency. Set `max_gen_tokens` and
`max_judge_tokens` independently for `m eval`.

`concurrency_budget` improves wall-clock latency only when the backend/provider
supports concurrent calls. It can consume the full budget before an early
success is observed, reorder history, increase rate-limit pressure, and make
seeded comparisons less reproducible. Start at `1`; raise it only after
measuring.

## Seeds and deterministic gates

Pass a backend-supported seed through `model_options`, for example
`model_options={"seed": 42}`. A seed is not a cross-provider reproducibility
contract. Compare fixed prompts, backend/model version, model options,
strategy, budgets, requirements, and output normalization before attributing a
change to the sampling policy.

Use deterministic checks as gates:

- JSON parsing, regex, line/word counts, schema validation, AST parsing,
  graph constraints, exact numeric normalization, and import inspection.
- A custom validator should return a targeted `reason`, not only `False`.
- Use `ValidationResult.score` to retain a measured value, but do not assume
  the sampling loop ranks by score; ordinary base strategies only use boolean
  pass/fail unless a custom strategy uses scores.

Use qualitative checks as labeled observations:

- semantic quality, helpfulness, style, groundedness requiring model judgment,
  and LLM-as-a-judge outputs;
- aLoRA/adapter scores, whose availability and schema are backend/model
  dependent;
- judge pass rates, which are not human-quality guarantees.

## Feedback choice

`RejectionSamplingStrategy` retries from the original action/context. It is a
useful baseline because it changes less than a repair policy. A
`RepairTemplateStrategy` includes failed `ValidationResult.reason` text in a
new `Instruction` copy. `MultiTurnStrategy` adds a user `Message` to a
`ChatContext` and therefore preserves conversation history. Reasons should be
specific, short, and actionable; avoid echoing secrets or full generated
artifacts.

For code generation, prefer `python_code_generation_sampling()` instead of
hand-copying its requirement list. Start with static validation. If actual
execution is required, use an explicit `execution_tier` policy and constrain
imports, timeout, output size, filesystem, and network according to the
capability policy. A failed execution must be treated as a failed candidate,
not as evidence that a retry is safe.

## SOFAI operating choices

- `fresh_start`: isolate S2 from S1 history; good when a bad repair trail may
  anchor the larger model.
- `continue_chat`: retain the full S1 dialogue; good when context is valuable,
  but costs more prompt tokens.
- `best_attempt`: pass S2 the best S1 attempt and failure summary; good when the
  S2 solver should see concrete progress without the entire transcript.

`feedback_strategy="simple"` gives a binary repair signal; `first_error`
limits feedback to the first issue; `all_errors` is more complete but increases
prompt length. Early escalation when the failed requirement set repeats is an
implementation behavior, not a quality guarantee.

## Majority voting caveats

Math MBRD parses and verifies equivalent expressions. Rouge-L scores lexical
sequence overlap. The selected candidate maximizes similarity to the sample
set, so consensus can amplify a common wrong answer. Add a deterministic
verifier or reference check whenever correctness is required. The current
weighted option does not add meaningful sample weights.

## What to record

For each run, persist: task/dataset identifier, candidate and judge backend/model
identifiers, model options including seed, strategy class and constructor
parameters, number of attempts, selected index, `SamplingResult.success`, all
requirement names and reasons, token/latency/cost metrics if enabled, and
whether a result was qualitative. Never report only the winning output when
failure analysis or benchmark comparison matters.
