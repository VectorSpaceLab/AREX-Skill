# Tools and Actions Troubleshooting

Start with the exact error text. Browser Use intentionally returns many web/action failures as `ActionResult(error=...)` so the agent can recover instead of crashing.

## Install and Import

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: browser_use` | Package not installed in the active environment | Install with `uv pip install browser-use` or use the project environment |
| `ImportError` for document/PDF readers | Optional file dependency missing | Install the relevant extra/dependency or avoid that file type |
| Browser/Chromium launch failure | Browser dependency not installed | Use Browser Use install guidance or route setup to `../../browser-control/SKILL.md` |
| Missing API key for the LLM | Provider credentials absent | Prefer `ChatBrowserUse` and set `BROWSER_USE_API_KEY`, or route provider setup to `../../llm-and-output/SKILL.md` |

## Registry and Validation

| Symptom | Cause | Fix |
| --- | --- | --- |
| `kwargs ... not allowed` | Custom action defines `**kwargs` | Replace with explicit parameters or a Pydantic `param_model` |
| `conflicts with special argument ... browser_session` | A special injected name has the wrong type | Use `browser_session: BrowserSession` or rename the ordinary parameter |
| `requires browser_session but none provided` | Direct action/registry call did not pass a session | Run through `Agent(..., tools=tools)` or pass `browser_session` in the direct call |
| `requires page_extraction_llm but none provided` | Action asks for extraction LLM outside an agent context | Pass `page_extraction_llm` or route extraction/model setup to `../../llm-and-output/SKILL.md` |
| `Invalid parameters ... for action` | Pydantic schema rejected action input | Inspect the action model schema; add `Field(...)` constraints/descriptions; run `scripts/validate_custom_tool.py` |
| Decorated action rejects positional args | Registry normalizes to keyword-only calls | Call `await action(params=Params(...), browser_session=session)` |
| Action is missing from prompt | Excluded action or domain filter not matching current URL | Check `exclude_actions`, `tools.exclude_action`, and `allowed_domains` patterns |

Validation command:

```bash
python skills/disco/browser-use/sub-skills/tools-and-actions/scripts/validate_custom_tool.py
```

## Default Action Failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Element index ... not available` | Page state changed after observation | Wait, refresh state, search page text, or re-select the element |
| `Cannot click on <select>` | Native dropdown requires dropdown action | Use `dropdown_options` then `select_dropdown` |
| File input click blocked | Upload inputs are guarded | Use `upload_file`, not `click` |
| Typed value differs from expected | Page reformatted/autocompleted input | Read the actual value, wait for suggestions, or click the intended suggestion |
| `Unsupported search engine` | Engine is not `duckduckgo`, `google`, or `bing` | Use a supported engine; prefer `duckduckgo` |
| `JavaScript Execution Failed` | Invalid JS or inaccessible DOM | Wrap code in an IIFE with try/catch; use browser APIs only |
| Action timed out after N seconds | Hung CDP/browser connection or slow action | Retry, restart/recreate browser session, or route browser diagnosis to `../../browser-control/SKILL.md` |

## File and Upload Failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `File path ... is not available` | Upload/read path not in `available_file_paths`, downloads, or managed files | Add the file to `Agent(..., available_file_paths=[...])` or create it with `write_file` |
| `File ... does not exist` | Local upload path is absent | Confirm the path exists before running the agent |
| `File ... is empty (0 bytes)` | Upload source is empty | Regenerate or choose a non-empty file |
| `Cannot write binary/image file` | `write_file` used for an image/binary extension | Use screenshot/browser download mechanisms; do not write binary through `write_file` |
| `Unsupported file extension` | Extension not supported by managed `FileSystem` | Rename to a supported text/document extension or use user-provided external file handling |
| `old_str not found` or replacement fails | `replace_file` exact match missing | `read_file` first and use the exact substring |
| Traversal or absolute path rejected | Managed file system containment guard | Use managed filenames only or explicit `available_file_paths` |

## Sensitive Data Failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| Placeholder remains as `<secret>password</secret>` | Missing/empty key or domain mismatch | Check key spelling, non-empty value, and current URL/domain pattern |
| Warning about no `allowed_domains` | Secrets could be exposed to arbitrary sites | Configure `Browser(allowed_domains=[...])` |
| Domain pattern not covered | `sensitive_data` domain is broader/different than browser allowlist | Align `sensitive_data` domain patterns with `allowed_domains` |
| TOTP code not generated | Key does not end in `bu_2fa_code` or secret is invalid | Use a valid Base32 TOTP secret and key suffix such as `login_bu_2fa_code` |
| Secret appears in custom action output | Action returned raw secret | Redact output; put only labels or success summaries in `ActionResult` |

## Security Guardrail Debugging

- Domain filters: use exact schemes when necessary; remember plain `example.com` means HTTPS by default.
- Unsafe wildcard TLDs like `example.*` do not match.
- `allowed_domains=[]` can be unsafe or semantically different from `None` in surrounding integrations; prefer explicit intended domains or omit only when unrestricted browsing is deliberate.
- If a user asks to bypass domain/file restrictions, explain the risk and propose a scoped allowlist or explicit file path instead.

## Workflow-Specific Recovery

### Custom 2FA Tool Fails

1. Confirm whether the user uses `sensitive_data` TOTP (`*_bu_2fa_code`) or a custom action.
2. If custom action, ensure it returns `ActionResult(extracted_content='...')` without logging the secret.
3. Ensure the task tells the agent to use that action, not scrape the page.
4. Pair login domain with `Browser(allowed_domains=[...])`.

### Upload Workflow Fails

1. Confirm `available_file_paths` contains the exact local path for local browsers.
2. Confirm the browser is local vs remote; remote paths must exist on the remote machine.
3. Confirm the selected index is near a file input; if not, ask the agent to identify the upload control first.
4. If the file was generated by the agent, use its managed filename, not a traversal/absolute path.

### Custom Browser Action Fails

1. Check injected parameter name: `browser_session`, not `browser` or `page`.
2. Check whether a built-in default action already covers the behavior.
3. Return recoverable `ActionResult(error=...)` for expected page/app states.
4. Keep low-level session/CDP startup fixes in `../../browser-control/SKILL.md`.
