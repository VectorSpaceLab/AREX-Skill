# Review Checklist

Use this checklist before handing off repository changes or when asked to review a local diff. Prefer focused evidence over broad rewrites, and do not modify code during a read-only review unless the user explicitly asks for fixes.

## 1. Scope and Intent

- Identify changed files with `git status` and `git diff`.
- Classify the change: bug fix, public API, workflow/runtime behavior, CLI/config, tooling, tests, docs, samples, packaging, or dependency update.
- Verify the implementation addresses the root cause rather than masking symptoms.
- Check that the change is minimal and does not refactor unrelated areas.

## 2. Architecture and Public Contracts

- Preserve ADK vocabulary: `Agent`/`LlmAgent`, `Workflow`, `Runner`, `App`, `Context`, `Event`, `ToolContext`, sessions, memory, artifacts, plugins, and CLI.
- If changing `Agent`, `Workflow`, `Runner`, `FunctionTool`, config models, CLI options, or serialized payloads, verify backwards compatibility and update tests/docs/schema as needed.
- Known public facts to keep in mind:
  - `Agent` accepts fields such as `name`, `description`, `rerun_on_resume`, `wait_for_output`, `schemas`, `sub_agents`, callbacks, `model`, `instruction`, `tools`, `generate_content_config`, `mode`, `output_key`, `planner`, `code_executor`, and tool/model callbacks.
  - `Workflow` accepts fields such as `name`, `schemas`, `edges`, `max_concurrency`, and `graph`.
  - `Runner.run` requires keyword arguments `user_id`, `session_id`, and `new_message`, with optional `state_delta` and `run_config`.
  - `FunctionTool(func, require_confirmation=False)` is valid in the installed package.
- For workflow or HITL changes, review event flow, checkpoint/resume behavior, `rerun_on_resume`, node output routing, branch isolation, and concurrency safety.
- For runtime service changes, review lifecycle ownership, cleanup, event persistence, and plugin/callback ordering.
- For CLI changes, review command help, app discovery, YAML/Python config compatibility, API server behavior, and schema impact.

## 3. Style and Code Quality

- Run or request focused formatter/linter checks: `pre-commit run --files <files>`, `pyink`, `isort`, `ruff check`, and `mypy` as appropriate.
- Verify 2-space indentation, 80-character formatting, and import grouping.
- Source files under `src/google/adk/` should use relative imports inside the framework and direct module imports rather than package-level `__init__.py` imports.
- Tests should use absolute imports from `google.adk`.
- Non-CLI framework code must not import from `google.adk.cli` internals.
- New source modules should be private-by-default with a leading underscore; expose public symbols through package `__init__.py` and `__all__` when intended.
- Use lazy logging templates: `logging.info("Message %s", value)`, not f-strings.
- Avoid logging secrets, credentials, model prompts containing private data, or personally identifiable information.
- Catch specific exceptions and include useful context; avoid bare `except:`.
- Keep async functions non-blocking; wrap synchronous I/O with `asyncio.to_thread` when needed.

## 4. Typing and Pydantic

- Ensure new functions and methods have explicit argument and return annotations.
- Avoid broad `Any`; prefer specific types, generics, protocols, or abstract collection types.
- Use `X | None` for new code when consistent with the surrounding file.
- Use keyword-only arguments where positional confusion is likely.
- Avoid mutable default values.
- For Pydantic v2 models, prefer `Field`, `PrivateAttr`, `model_post_init`, `model_dump`, `field_validator`, and `model_validator` patterns.
- For on-wire models, confirm camelCase serialization behavior via `SerializedBaseModel` when applicable.
- If model field docstrings feed schema descriptions, check generated config/schema diffs.

## 5. Test Coverage and Quality

- Every behavior change should have a focused unit or integration test unless there is a clear reason not to.
- Tests should exercise public behavior, not private implementation details.
- Test names should describe observed behavior.
- Test docstrings should state what the caller observes; complex tests should explain Setup/Act/Assert.
- Use real ADK components when practical, and mock external boundaries such as LLM APIs, cloud providers, databases, and network services.
- Avoid kitchen-sink fixtures and unrelated assertions.
- For runner, workflow, event, and resume changes, add tests covering interruptions, output events, state deltas, and resumed execution where relevant.
- For optional extras, include tests that make missing dependency behavior clear without requiring the extra in a base environment.

## 6. Docs, Guides, Samples, and Schema

Check whether the change requires documentation or sample updates:

- **Docs/guides**: update when public APIs, workflows, CLI behavior, config, serialized behavior, or recommended patterns change.
- **Unit guides**: create or update a detailed guide for new code units when developer-facing usage is not otherwise documented.
- **Samples**: add or update `contributing/samples/` when a capability benefits from a minimal runnable pattern.
- **Sample README**: include Overview, Sample Inputs, Graph where relevant, How To, and Related Guides.
- **Model defaults**: sample agents should not hardcode `model=` unless explicitly required.
- **Generated schema**: run `python scripts/generate_agent_config_schema.py` and review `AgentConfig.json` when config models, aliases, validators, or descriptions change.

## 7. Validation Plan

A good handoff names checks actually run and checks intentionally skipped:

- Focused tests selected by changed area, for example `pytest tests/unittests/workflow -q`.
- Relevant integration tests, for example CLI run/eval/app discovery tests.
- Formatter/linter/type checks relevant to touched files.
- Schema generation diff check when applicable.
- Docs/sample checks when examples or guides changed.
- Explicit skips for remote/cloud/model tests requiring credentials, network, deployed resources, optional extras, or long runtime.

Use the bundled selector for an initial validation proposal:

```bash
python skills/adk-python/sub-skills/repo-development/scripts/select_adk_tests.py <changed-files-or-capability-names>
```

## 8. Git Safety

- Do not run destructive operations such as `git reset --hard`, `git clean`, force-push, rebase, or branch deletion without explicit user approval.
- Do not commit unless the user asks.
- If asked to commit, use Conventional Commits: `<type>(<scope>): <description>`.
- The commit subject should explain the outcome or reason, not just the mechanics, and should use imperative mood with no trailing period.
- Include a short body when the subject alone cannot explain why the change was necessary.
