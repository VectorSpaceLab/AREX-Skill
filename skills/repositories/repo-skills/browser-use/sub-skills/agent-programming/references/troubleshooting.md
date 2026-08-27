# Agent Programming Troubleshooting

Start from the smallest failing script, then add browser settings, custom tools, structured output, and production integrations one at a time.

## Quick Triage

```python
history = await agent.run(max_steps=10)
print("done", history.is_done(), "success", history.is_successful())
print("result", history.final_result())
print("actions", history.action_names())
print("errors", [e for e in history.errors() if e])
print("urls", history.urls())
```

If the script fails before `history` exists, the issue is likely import/install, model credentials, browser startup, beta terminal startup, or constructor validation.

## Install or Import Failure

Symptoms:

- `ModuleNotFoundError: No module named 'browser_use'`
- Import of `browser_use.beta` works but beta run fails immediately.
- `browser-use` imports in one shell but not another.

Fixes:

```bash
python - <<'PY'
import browser_use
from browser_use import Agent, ChatBrowserUse
from browser_use.beta import Agent as BetaAgent
print(browser_use.__version__ if hasattr(browser_use, "__version__") else "browser-use imported")
print(Agent, ChatBrowserUse, BetaAgent)
PY
```

- Install into the same Python environment that runs the script.
- For beta/core workflows, install the native core extra or Browser Use Terminal for the target platform.
- In repo development, use the project’s `uv` workflow rather than ad-hoc `pip` installs.

## Missing API Key or Model Credential

Symptoms:

- Provider authentication error before the first browser action.
- Rate-limit or authorization errors in `history.errors()` or saved conversation logs.
- `ChatBrowserUse()` fails unless `BROWSER_USE_API_KEY` is configured.

Fixes:

- Confirm the relevant environment variable exists without printing its value.
- Use `ChatBrowserUse()` by default for Browser Use tasks when the user has a Browser Use key.
- Do not replace model names the user intentionally chose; only fix credential wiring or route to `../../llm-and-output/SKILL.md`.
- Keep `max_steps` small while validating credentials.

## Browser, Chromium, CDP, or Session Failure

Symptoms:

- Browser never opens or closes immediately.
- Initial navigation times out before any model step.
- CDP connection is refused or stale.
- The beta agent pre-navigation fails before SDK run.

Fixes:

- Route browser launch/profile/CDP details to `../../browser-control/SKILL.md`.
- For agent-level mitigation, set `step_timeout` and make first navigation explicit in `initial_actions`.
- If automatic URL extraction causes unwanted navigation, set `directly_open_url=False`.
- If using beta with an existing CDP session, remember initial actions are executed before SDK delegation.

## Beta Terminal/Core Failure

Symptoms:

- `BetaAgentError: Could not find browser-use-terminal...`
- `Rust SDK server pipe closed...`
- `Rust SDK server stdin is unavailable`
- `follow_up()` says no active Rust session.

Checks:

```bash
python - <<'PY'
from browser_use.beta import find_browser_use_terminal_binary, BetaAgentError
try:
    print(find_browser_use_terminal_binary())
except BetaAgentError as exc:
    print(exc)
PY
```

Fixes:

- Install `browser-use[core]` where supported or install Browser Use Terminal.
- Set `BROWSER_USE_TERMINAL_BINARY` only when pointing to a compatible binary that supports `sdk-server`.
- Use the legacy `browser_use.Agent` if beta/core runtime is unavailable and the user only needs Python agent automation.
- Call `await agent.run(...)` before `await agent.follow_up(...)`.

## Empty or Missing Final Result

Symptoms:

- `history.final_result()` returns `None`.
- `history.is_done()` is false after `run()` returns.
- The agent performed actions but did not call `done` with extracted content.

Fixes:

- Inspect `history.errors()` and `history.action_names()`.
- Make the task’s stop condition explicit: “Finish with done and include ...”.
- Increase `max_steps` only after confirming progress.
- If the final page is correct but no result is returned, add a prompt instruction to use the `done` action with the exact final answer.
- If a structured output schema is involved, route to `../../llm-and-output/SKILL.md` and validate final JSON.

## Initial Actions Fail or Run Unexpectedly

Symptoms:

- Error occurs before the first model output.
- First URL differs from expected URL.
- Beta task context includes setup actions the user did not expect.

Fixes:

- Print the configured initial actions before running.
- Use explicit `initial_actions=[{"navigate": {"url": "...", "new_tab": False}}]` for deterministic start.
- Set `directly_open_url=False` to prevent URL auto-detection from task text.
- Cap `step_timeout`; legacy run setup bounds initial actions by this timeout.
- In beta, check both `initial_action_payloads` and converted `initial_actions` when debugging action-name aliases.

## Planning Not Visible

Symptoms:

- No plan updates appear in model output.
- Tests or logs show `enable_planning` is false.
- Flash schema lacks `thinking`, `current_plan_item`, or `plan_update`.

Fixes:

- Check `agent.settings.flash_mode` and `agent.settings.enable_planning`.
- Set `flash_mode=False` with a model configuration that does not force it.
- Browser Use provider models currently force flash mode automatically, which disables planning.
- Use full mode for debugging, then switch back to flash mode for speed.

## Repeated Actions or Stalled Page

Symptoms:

- The same click/input/search repeats.
- URL and page content do not change for many steps.
- The agent keeps trying an element that is not interactable.

Fixes:

- Enable or keep `loop_detection_enabled=True` for nudges.
- Lower `planning_replan_on_stall` to trigger earlier replan context in full mode.
- Add prompt instructions for alternatives: keyboard navigation, scroll, refresh once, use search, or stop with reason.
- Route deterministic selector/action fixes to `../../tools-and-actions/SKILL.md`.
- Route DOM/iframe/viewport issues to `../../browser-control/SKILL.md`.

## Callback Problems

Symptoms:

- Run aborts after a logging callback.
- Callback gets `None` model output during replay or history-prefix callback.
- Host app freezes during callback.

Fixes:

- Make callbacks async-safe and fast.
- Handle `model_output is None` defensively.
- Do not perform slow network/file operations inline; enqueue work elsewhere.
- Use `register_should_stop_callback` for cancellation instead of raising from a progress callback.
- Never log raw secrets from prompts, forms, cookies, or `sensitive_data`.

## Validation Errors and Action Schema Mismatch

Symptoms:

- `Invalid model output format. Please follow the correct schema.`
- Initial action dictionary is ignored or fails during execution.
- Custom tool parameters fail Pydantic validation.

Fixes:

- Reduce `max_actions_per_step` while debugging.
- Keep `initial_actions` as one-action dictionaries with current action names such as `navigate`, `click`, and `input`.
- If using custom actions, route to `../../tools-and-actions/SKILL.md` for Pydantic action schemas and parameter injection rules.
- If using structured output, route to `../../llm-and-output/SKILL.md` and inspect raw `history.final_result()`.

## Security, Domain, and File Guardrails

Symptoms:

- Navigation is blocked despite a valid URL.
- File read/write/upload action is unavailable or denied.
- Sensitive data is not injected on a site.

Fixes:

- Route `allowed_domains`, `prohibited_domains`, file containment, and sensitive-data rules to `../../browser-control/SKILL.md` and `../../tools-and-actions/SKILL.md`.
- At the agent level, mention allowed domains and file constraints in the task so the model does not keep trying blocked actions.
- Use `available_file_paths` only for files the agent is allowed to access.

## Timeout Tuning

Symptoms:

- LLM call times out while page actions are fine.
- Browser action times out while model calls are fine.
- Initial actions time out before the main loop.

Fixes:

- Increase `llm_timeout` for slow reasoning models.
- Increase `step_timeout` for slow page loads or initial actions.
- Reduce page/task complexity and `max_actions_per_step` while isolating the cause.
- Use `final_response_after_failure=True` when you want a last best-effort answer after repeated failures.

## Conversation and History Debugging

Use conversation logs for prompt/model-output analysis:

```python
agent = Agent(task="...", llm=llm, save_conversation_path="logs/conversation.json")
```

Use history JSON for browser actions and results:

```python
history = await agent.run(max_steps=20)
history.save_to_file("logs/history.json")
```

Avoid uploading or sharing logs until secrets and personal data are redacted.
