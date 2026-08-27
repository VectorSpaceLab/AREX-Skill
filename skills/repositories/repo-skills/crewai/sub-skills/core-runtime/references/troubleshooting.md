# Core Runtime Troubleshooting

Start with static checks before running an LLM-backed crew. For JSONC projects, run `../scripts/validate_crew_definition.py`. For direct Python, instantiate `Agent`, `Task`, and `Crew` objects in a small script without calling `kickoff()` to trigger Pydantic validation safely.

## Agent Missing `role`, `goal`, or `backstory`

Symptoms:

- Agent construction fails with a validation error.
- JSONC agent file loads poorly or the crew cannot build the agent.

Likely causes:

- A JSONC agent file omits one of the three required fields.
- The field is misspelled or nested under an unsupported object.
- A placeholder was used as the whole value but no default/input will be provided.

Fix:

- Add non-empty `role`, `goal`, and `backstory` to each agent.
- Keep behavior options under `settings` or top-level public `Agent` fields.
- Run the validator to catch missing fields before `crewai run`.

## Task Missing `expected_output`

Symptoms:

- Task construction fails with `expected_output must be provided either directly or through config`.
- A JSONC task appears valid but CrewAI refuses to instantiate it.

Likely causes:

- `expected_output` was omitted because the description seemed sufficient.
- A classic YAML/task config was partially migrated to JSONC.

Fix:

- Give every task a concrete `expected_output` that defines the shape and quality bar for completion.
- Include output format instructions there when useful, but use `markdown=True`, `output_json`, or `output_pydantic` for runtime output behavior.

## Task Context Forward Reference

Symptoms:

- JSONC validation reports a task context reference to a later task.
- Sequential runs use missing or unexpected prior context.

Likely causes:

- A task's `context` includes a task name that appears later in `tasks`.
- A task `name` changed but dependent tasks still use the old name.
- The crew relies on implicit previous-task context when it should name a non-adjacent dependency.

Fix:

- Order tasks so producers appear before consumers.
- Use stable task names and update every `context` list after renames.
- In direct code, pass previous `Task` objects, not names.

## Hierarchical Process Without Manager

Symptoms:

- Crew construction raises an error that `manager_llm` or `manager_agent` is required.
- The crew works in sequential mode but fails after switching to hierarchical.

Likely causes:

- `process` is `hierarchical` but neither manager field is configured.
- A custom manager agent is included in the normal `agents` list.
- The manager agent is configured with assumptions that conflict with manager validation.

Fix:

- Add `manager_llm` or `manager_agent`.
- Keep a custom `manager_agent` outside the `agents` list.
- Let the manager delegate; avoid over-constraining every hierarchical task unless the workflow intentionally mixes manager assignment with explicit task agents.
- Route provider credential/model setup to `../llm-and-providers/SKILL.md`.

## Untrusted Python Callback or Custom Tool Reference

Symptoms:

- JSONC review finds `{"python": "module.attribute"}` or `custom:<name>` entries.
- A crew project from an unknown source wants to load local Python during validation.

Likely causes:

- JSONC callbacks point to local modules.
- Custom tools under `tools/` are loaded by name.
- A project was copied from an untrusted source.

Fix:

- Do not run untrusted JSONC projects.
- Use the bundled validator because it reports these references without importing them.
- Review the target Python module before execution.
- Route tool implementation and MCP details to `../tools-and-mcp/SKILL.md`.

## `output_json` and `output_pydantic` Confusion

Symptoms:

- Task construction raises `Only one output type can be set, either output_pydantic or output_json`.
- Downstream code expects `json_dict` but only `pydantic` is populated, or vice versa.
- `.json` access fails because the output format is not JSON.

Likely causes:

- Both structured fields are set on one task.
- A direct-code Pydantic model was migrated to JSONC without deciding JSON vs Pydantic output behavior.
- A downstream task assumes every structured output becomes a dictionary.

Fix:

- Use `output_json=Model` for dictionary/JSON workflows.
- Use `output_pydantic=Model` for model-object workflows.
- Check `TaskOutput.output_format`, `json_dict`, and `pydantic` before consuming output.
- Use `to_dict()` when callers can accept either structured form.

## Guardrail Retry Mistakes

Symptoms:

- Runtime raises `Task failed guardrail validation after N retries`.
- Multiple guardrails retry unexpectedly or one guardrail appears ignored.
- String guardrails fail before running because no valid agent LLM is available.

Likely causes:

- Guardrail returns `None`, the wrong tuple shape, or vague failure feedback.
- `guardrails` is supplied, so the single `guardrail` field is ignored.
- `guardrail_max_retries` is too high for an expensive LLM-backed correction loop.
- String guardrails require an assigned agent and concrete `BaseLLM` instance.

Fix:

- Function guardrails should accept one output object and return `(True, value)` or `(False, actionable_feedback)`.
- Prefer deterministic function guardrails for exact checks.
- Keep `guardrail_max_retries` small, often `1` or `2` during debugging.
- If mixing guardrails, remember they run in order and each guardrail sees the previous guardrail's output.

## Callback Does Not Fire or Fires Twice

Symptoms:

- Crew-level `step_callback` does not run for one agent.
- Both task-level and crew-level task callbacks appear in logs.
- Callback side effects happen again after retry, replay, or resume.

Likely causes:

- Agent-specific `step_callback` overrides the crew-level step callback for that agent.
- Task-specific `callback` and crew `task_callback` can both be involved when distinct.
- Callback code is not idempotent.

Fix:

- Put step monitoring at the most specific level that needs it.
- Make callbacks idempotent and safe to repeat.
- Avoid irreversible side effects in callbacks unless they are guarded by run/task IDs.
- Use observability hooks for tracing use cases; see `../observability-and-hooks/SKILL.md`.

## Planning Uses an Unexpected Model

Symptoms:

- Enabling `planning=True` triggers a provider/API-key error before normal tasks run.
- A crew uses a non-OpenAI agent model but planning still tries an OpenAI default.

Likely causes:

- `planning_llm` was omitted.
- The default planner model requires credentials that are not configured.

Fix:

- Set `planning_llm` explicitly when enabling planning.
- Keep provider credentials and base URL setup in `../llm-and-providers/SKILL.md`.
- Disable planning while debugging base task wiring.

## Reasoning Changes Task Prompting

Symptoms:

- Task descriptions include extra reasoning-plan content.
- A reasoning failure is logged but task execution continues.

Likely causes:

- `Agent(reasoning=True)` injects a reasoning plan into execution.
- Reasoning errors are designed to be non-fatal.

Fix:

- Use `max_reasoning_attempts` to bound the pre-task reasoning loop.
- Disable `reasoning` for deterministic prompt comparison tests.
- Treat reasoning as an LLM-backed enhancement, not as a static validation feature.

## Checkpoint, Replay, and Training File Confusion

Symptoms:

- A user expects checkpoint files to be the same as replay history.
- A crew resumes with old task outputs after a code/config change.
- Training file paths are mixed with checkpoint restore paths.

Likely causes:

- Checkpointing, CLI replay, and training are separate mechanisms.
- A checkpoint captures runtime state and may skip already completed tasks.
- Replay and training are CLI/project workflows with different storage and commands.

Fix:

- Use `checkpoint=True` or `CheckpointConfig` for resume/fork state.
- Use `Crew.from_checkpoint(CheckpointConfig(restore_from=...))` for checkpoint resume.
- Use CLI replay/training guidance in `../cli-and-projects/SKILL.md` when the request mentions commands such as `crewai replay`, `crewai train`, or saved training outputs.
- Regenerate checkpoints after changing task order, task names, output model classes, or callback code.

## Output File Surprises

Symptoms:

- Task output is written to an unexpected path.
- Parent directories are created automatically.
- Placeholder values appear in filenames.

Likely causes:

- `output_file` uses relative paths from the process working directory.
- `create_directory` defaults to `True`.
- Placeholder inputs were missing or different from expected.

Fix:

- Use explicit safe relative output paths such as `output/report.md`.
- Set `create_directory=False` when automatic directory creation is not desired.
- Validate placeholders against `inputs` before kickoff.

## Static Validator Reports Warnings but Exits Zero

Symptoms:

- The validator prints trust warnings for Python callbacks or custom tools and still exits `0`.

Likely causes:

- The shape is valid, but runtime execution would import local Python.

Fix:

- Treat warnings as manual review items.
- Use `--strict-warnings` to make warnings fail CI or a pre-run gate.
- Do not run untrusted callback/tool references until reviewed.
