# Security and File Operations

This reference covers action-level guardrails for secrets, file reads/writes, and uploads. Browser/session domain configuration belongs in `../../browser-control/SKILL.md`; production credential stores and cloud deployment belong in `../../production-integrations/SKILL.md`.

## Sensitive Data Pattern

Pass secrets via `Agent(..., sensitive_data=...)` and refer to them by placeholder in tasks or model-produced action input.

```python
from browser_use import Agent, Browser, ChatBrowserUse

sensitive_data = {
    'https://accounts.example.com': {
        'username': 'user@example.com',
        'password': 'not-in-task-text',
        'login_bu_2fa_code': 'BASE32TOTPSECRET',
    }
}

browser = Browser(allowed_domains=['https://accounts.example.com'])
agent = Agent(
    task='Login using <secret>username</secret>, <secret>password</secret>, and the 2FA placeholder when requested.',
    llm=ChatBrowserUse(),
    browser=browser,
    sensitive_data=sensitive_data,
)
```

Behavior verified from the registry and security tests:

- Placeholder format is `<secret>key</secret>`.
- Domain-specific format is `{domain_pattern: {key: value}}`.
- Domain-specific secrets are exposed only when the current URL matches the domain pattern.
- Legacy flat format `{key: value}` is accepted but exposes those secrets on all domains; avoid it for web login workflows.
- Empty secret values are treated as missing.
- Missing placeholders are preserved and logged as missing rather than silently replaced.
- Keys ending in `bu_2fa_code` are treated as TOTP secrets and converted to a current six-digit code.
- Browser Use filters sensitive values from messages/history by replacing observed secret values with placeholders.

## Secret Guardrails

- Always pair `sensitive_data` with `Browser(allowed_domains=[...])` for credentialed workflows.
- Use exact domain patterns; avoid broad wildcards.
- Do not include raw secret values in task strings, action descriptions, logs, filenames, or `long_term_memory`.
- When a user reports that a secret was not typed, check placeholder spelling, non-empty value, current URL, and domain coverage.
- If a user needs app-specific 2FA retrieval from an authenticator, implement a custom action that returns an `ActionResult`; do not scrape 2FA codes from pages.

## Domain Pattern Facts

Browser Use domain matching supports patterns such as:

- `example.com`: defaults to `https://example.com`.
- `http://example.com`: explicit HTTP only.
- `http*://example.com`: HTTP or HTTPS.
- `*.example.com`: base domain and subdomains over HTTPS.
- `chrome-extension://*`: extension pages.

Unsafe or invalid patterns do not match, including wildcard TLDs like `example.*`, malformed URLs, and broad embedded wildcards such as `*google.com`.

## Managed File Operations

Default file actions use Browser Use's managed `FileSystem`.

### `write_file`

```python
# As an agent action: write_file(file_name='report.md', content='# Report')
```

Rules:

- Overwrites by default.
- Use `append=True` to append.
- Use `trailing_newline=False` when exact final bytes matter.
- Supported extensions include `.txt`, `.md`, `.json`, `.jsonl`, `.csv`, `.html`, `.xml`, `.pdf`, and `.docx`.
- Binary/image extensions such as `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.mp4`, `.zip`, and `.exe` are rejected.
- CSV content is normalized through Python's CSV handling to repair common quoting/newline mistakes.
- Filenames are sanitized or rejected for unsafe names; path traversal and absolute-path attempts are refused by the managed file system.

### `read_file`

`read_file` can read:

- Managed files written by the agent.
- User-supplied files listed in `available_file_paths`.
- Downloaded files that Browser Use has tracked.
- Supported documents and images where file readers are available.

Large text is summarized in `long_term_memory`, while full content remains in `extracted_content` for the current step.

### `replace_file`

Use for targeted edits:

```python
# replace_file(file_name='todo.md', old_str='- [ ] Submit', new_str='- [x] Submit')
```

Read the file first when `old_str` may not be exact.

## Upload Files Safely

`upload_file(index, path)` uploads through a file input near the indexed element.

Allowed sources:

- A path in `Agent(..., available_file_paths=[...])`.
- A file downloaded during the Browser Use session.
- A managed FileSystem file by filename.
- A remote path when `browser_session.is_local` is false and the remote browser can access that path.

Local-browser checks:

- File must exist.
- File must be non-empty.
- Managed FileSystem upload paths are resolved from the FileSystem-owned basename, not from agent-controlled traversal text.
- Resolved upload paths must remain inside the managed FileSystem directory.

Security implication: if the agent passes `../note.md` and a managed `note.md` exists, Browser Use resolves only the safe managed basename and containment-checks the result. If there is no safe source, the action returns an availability error.

## Available File Paths

When users need to upload or read a local file:

```python
agent = Agent(
    task='Upload the provided invoice PDF to the form',
    llm=ChatBrowserUse(),
    available_file_paths=['/path/to/invoice.pdf'],
)
```

Do not tell future agents to guess or discover arbitrary user files. Require explicit user-provided paths.

## Action-Level Security Checklist

Before shipping a custom action:

- Does it need `allowed_domains`?
- Does it mutate external systems? If yes, require confirmation or make it domain-scoped.
- Does it accept file paths? Validate basename, extension, and containment.
- Does it return secrets? Redact or summarize instead.
- Does it call browser JavaScript? Limit to browser APIs and output size.
- Does it need a browser? Use `browser_session` exactly.
- Does it need a local/remote browser distinction? Route browser setup to `../../browser-control/SKILL.md`.
