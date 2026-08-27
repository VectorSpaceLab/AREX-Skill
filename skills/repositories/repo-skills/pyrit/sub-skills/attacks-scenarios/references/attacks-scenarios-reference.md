# Attack, Executor, Scenario, and Technique Workflows

## Workflow selection

- Use `PromptSendingAttack` for a single objective prompt or a deterministic no-secret dry run.
- Use `MultiPromptSendingAttack` or prepended conversation configuration for fixed multi-message scripts.
- Use adaptive attacks such as Crescendo, TAP/tree-of-attacks, PAIR, or red-teaming when the next prompt depends on prior responses and scorer feedback.
- Use `SequentialAttack` when several child attacks are attempted as fallbacks for the same objective.
- Use a `Scenario` when the task is a campaign over datasets, attack techniques, targets, and scoring defaults.
- Use benchmark/workflow executors when the output is a structured benchmark result rather than a single adversarial conversation.

## Minimal planning checklist

1. Define the objective and scope of allowed red-team behavior.
2. Select or configure the objective target in `targets-scorers`.
3. Choose the seed objectives/datasets in `converters-datasets`.
4. Choose converters and ensure target modality compatibility.
5. Choose scorers; define success, failure, and `UNDETERMINED` handling.
6. Initialize PyRIT memory/config using `setup-memory-core`.
7. Bound concurrency, retries, and maximum attempts before live sends.
8. Plan result rendering and memory labels for later lookup.

## Scenario campaign pattern

A scenario packages datasets and attack techniques; it should not hide target credentials or invent scorer defaults. Use initializers to register configured targets/scorers/techniques, then run the scenario through code or through `pyrit_scan`.

For CLI execution, keep semantic choices here but route command construction to `cli-backend-scanner` so flags and backend lifecycle are correct.

## Results

Attack and scenario results should be persisted through memory and rendered with output helpers. If a result is missing, check the scenario result ID, attack result IDs, memory labels, and whether the run completed or was cancelled.

## Safe no-secret dry run design

A future agent can validate orchestration without a live model by planning around `TextTarget`, offline converters, and a rule scorer. This proves wiring and signatures only; it is not evidence of model robustness.
