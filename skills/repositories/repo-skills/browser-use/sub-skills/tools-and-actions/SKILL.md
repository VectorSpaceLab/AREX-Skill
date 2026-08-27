---
name: tools-and-actions
description: "Build and debug Browser Use tools/actions: custom Tools/Controller
  actions, default browser/file actions, ActionResult returns, parameter
  injection, sensitive data, security guardrails, and validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tools and Actions

Use this sub-skill when the user needs Browser Use actions, custom tools, file operations, upload/download handling, sensitive data placeholders, or action validation. Prefer `ChatBrowserUse` in examples unless the user already chose another model.

## Route Here

- User asks to add `@tools.action(...)`, `Tools()`, `Controller`, custom actions, action filters, 2FA helpers, human-in-the-loop actions, deterministic browser helpers, or direct `tools.<action>()` calls.
- User asks which default actions exist, how to remove actions, or why an action schema/model is rejected.
- User asks about `ActionResult`, `extracted_content`, `long_term_memory`, `error`, `is_done`, `success`, attachments/images, or completion semantics.
- User asks about `available_file_paths`, `write_file`, `read_file`, `replace_file`, `upload_file`, downloaded files, or file containment errors.
- User asks how `sensitive_data` works, how to use `<secret>name</secret>`, or how to keep secrets scoped to allowed domains.
- User hit tool validation, parameter injection, domain filter, file upload, or security guardrail failures.

## Route Elsewhere

- Agent construction, task prompting, run loops, history inspection, callbacks, initial actions, or Python workflow structure: `../agent-programming/SKILL.md`.
- Browser/Profile/CDP/session/proxy/download directory/domain navigation configuration: `../browser-control/SKILL.md`.
- LLM adapters, structured output models, extraction LLMs, cost, fallback models, or provider credentials: `../llm-and-output/SKILL.md`.
- Terminal `browser-use` / `bu` CLI sessions and CLI upload commands: `../cli-and-sessions/SKILL.md`.
- Cloud/sandbox/MCP/skills/telemetry/production integrations: `../production-integrations/SKILL.md`.

## Safe Defaults

- Import `Tools`, `ActionResult`, and `BrowserSession` from `browser_use`; `Controller` is a backwards-compatible alias for `Tools`.
- Use Pydantic v2 models for complex custom action input; keep action function parameters explicit and typed.
- Name injected browser parameters exactly `browser_session`, `page_extraction_llm`, `file_system`, `available_file_paths`, `page_url`, `cdp_client`, `has_sensitive_data`, `extraction_schema`, or `context`.
- Do not define `**kwargs` on a custom action; the registry rejects it. Use explicit parameters or a Pydantic `param_model`.
- Return `ActionResult` when the agent needs reasoning context, memory, errors, completion status, files, or attachments; simple strings are accepted but less expressive.
- Scope dangerous or credentialed custom actions with `allowed_domains=[...]` when possible.
- Use `Tools(exclude_actions=[...])` or `tools.exclude_action(name)` to remove defaults that do not fit the task.
- Pass user-provided upload files through `Agent(..., available_file_paths=[...])`; never invent local paths.
- Use `sensitive_data` placeholders instead of embedding passwords or API keys in tasks.

## Minimal Custom Tool

```python
from browser_use import ActionResult, Agent, BrowserSession, ChatBrowserUse, Tools

tools = Tools()

@tools.action('Ask the user for a one-line confirmation')
async def ask_user(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'User answered: {answer}')

agent = Agent(task='Ask for confirmation, then continue', llm=ChatBrowserUse(), tools=tools)
```

For browser-aware actions, use the exact injected name:

```python
@tools.action('Read current page URL')
async def current_url(browser_session: BrowserSession) -> ActionResult:
    url = await browser_session.get_current_page_url()
    return ActionResult(extracted_content=url, long_term_memory=f'Current URL: {url}')
```

## Custom Action Patterns

- Loose parameters: `async def fill_field(index: int, text: str, browser_session: BrowserSession)`; Browser Use auto-generates a Pydantic model for non-special parameters.
- Pydantic model first: define a model and pass `param_model=MyParams`, then write `async def action(params: MyParams, browser_session: BrowserSession)`.
- Domain-filtered action: `@tools.action('Use only on billing pages', allowed_domains=['https://billing.example.com'])`.
- Sequence-ending action: pass `terminates_sequence=True` for navigation-like actions where queued multi-actions should stop after execution.
- Direct call in tests/debugging: many registered actions can be called as `await tools.read_file(file_name='x.md', browser_session=session, file_system=fs, available_file_paths=[])`.

See [references/custom-tools.md](references/custom-tools.md) for full patterns and validation rules.

## Default Actions

Core defaults include:

- Navigation and tabs: `search`, `navigate`, `go_back`, `wait`, `switch`, `close`.
- Page interaction: `click`, `input`, `upload_file`, `scroll`, `find_text`, `send_keys`, dropdown actions.
- Page content: `extract`, `search_page`, `find_elements`, `evaluate`, `screenshot`, `save_pdf`.
- File operations: `write_file`, `read_file`, `replace_file`.
- Completion: `done` or structured done when `output_model` is configured.

See [references/default-actions.md](references/default-actions.md) for action parameters, when to exclude defaults, JavaScript evaluation cautions, and file-action behavior.

## File and Secret Guardrails

- `write_file` supports text/document outputs such as `.txt`, `.md`, `.json`, `.jsonl`, `.csv`, `.html`, `.xml`, `.pdf`, and `.docx`; it rejects binary/image extensions such as `.png` and `.jpg`.
- `replace_file` requires exact `old_str`; read the file first when unsure.
- `read_file` can read managed files and user/downloaded files from `available_file_paths`; large content is summarized in memory but full content is returned for the current step.
- `upload_file` accepts paths from `available_file_paths`, Browser Use downloads, remote-browser paths, or managed FileSystem files; local uploads are checked for existence and nonzero size.
- Sensitive values are provided as `sensitive_data` and referenced as `<secret>key</secret>`; domain-specific secrets are only exposed on matching URLs.
- Pair `sensitive_data` with `Browser(..., allowed_domains=[...])` for prompt-injection resistance.

See [references/security-and-files.md](references/security-and-files.md) for guardrail details and examples.

## Validate Before Shipping

Run the bundled helper after editing tool code or snippets:

```bash
python skills/disco/browser-use/sub-skills/tools-and-actions/scripts/validate_custom_tool.py
```

The helper checks imports, registry schema generation, injected parameter names, validation errors, domain filtering, and `ActionResult` normalization without launching a browser or making network calls.

## Troubleshooting First Moves

- Import failure: verify package install and use `uv pip install browser-use`; install Chromium separately when the task needs a live browser.
- `requires browser_session but none provided`: use the tool through `Agent(..., tools=tools)` or pass `browser_session` in direct tests.
- `conflicts with special argument`: rename the parameter or use the required special type, usually `BrowserSession`.
- Invalid parameters: inspect the generated Pydantic schema or run `validate_custom_tool.py`.
- File upload unavailable: add the path to `available_file_paths` or write/read through the managed file system first.
- Secrets not substituted: confirm placeholder spelling, non-empty values, matching domain pattern, and `allowed_domains` coverage.
- CDP/browser action timeout: retry, restart the browser/session, or route session setup to `../browser-control/SKILL.md`.

See [references/troubleshooting.md](references/troubleshooting.md) for symptom-to-fix tables.

## Hard Case Prompts This Sub-skill Should Handle

- Build an authenticated data-entry agent with domain-scoped secrets, a custom 2FA action, file upload from `available_file_paths`, and structured status messages; route browser profile setup to `../browser-control/SKILL.md` and output schema setup to `../llm-and-output/SKILL.md`.
- Debug a failing custom action that uses `browser` instead of `browser_session`, has `**kwargs`, tries to upload `../note.md`, and leaks a password in history; produce safe corrected code and validation steps.
