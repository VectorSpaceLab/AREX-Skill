# Default Actions Reference

`Tools()` registers Browser Use's default action set. Use `Tools(exclude_actions=[...])` to remove actions at construction time or `tools.exclude_action(name)` after construction.

## Action Groups

| Group | Actions | Primary use |
| --- | --- | --- |
| Navigation | `search`, `navigate`, `go_back`, `wait` | Search, open URLs, recover from load timing, back navigation |
| Tabs | `switch`, `close` | Move between browser tabs using 4-character tab IDs |
| Page interaction | `click`, `input`, `scroll`, `find_text`, `send_keys` | Interact with indexed DOM elements and keyboard shortcuts |
| Forms/files | `upload_file`, `dropdown_options`, `select_dropdown` | File inputs and select/dropdown controls |
| Page content | `extract`, `search_page`, `find_elements`, `evaluate` | LLM extraction, DOM search, CSS querying, JavaScript execution |
| Visual/document | `screenshot`, `save_pdf` | Visual state request, PDF export |
| File system | `write_file`, `read_file`, `replace_file` | Managed files and user/downloaded files |
| Completion | `done` or structured output action | Final response and optional files-to-display |

## High-Value Parameters

- `search(query, engine='duckduckgo')`: DuckDuckGo is the safe default because it tends to trigger fewer captchas; Google and Bing are available.
- `navigate(url, new_tab=False)`: sequence-terminating; can retry empty DOM loads and returns recoverable `ActionResult(error=...)` for common network failures.
- `click(index)`: index-only by default; coordinate support can be enabled by Browser Use for capable models or through tool configuration.
- `input(index, text, clear=True)`: clears existing text by default; `text=''` clears a field; `clear=False` appends.
- `upload_file(index, path)`: `path` must be available through `available_file_paths`, downloaded files, a remote browser path, or a managed file.
- `scroll(down=True, pages=1.0, index=None)`: use `index` to scroll inside a scrollable element.
- `send_keys(keys)`: supports keys like `Enter`, `Escape`, `PageDown`, and shortcuts such as `Control+o`.
- `extract(query, extract_links=False, extract_images=False, start_from_char=0, output_schema=None, already_collected=[])`: use for LLM-backed page extraction; route model/output schema design to `../../llm-and-output/SKILL.md`.
- `search_page(pattern, regex=False, case_sensitive=False, context_chars=150, css_scope=None, max_results=25)`: deterministic text search in page content.
- `find_elements(selector, attributes=None, max_results=50, include_text=True)`: deterministic CSS selection for tags/text/attributes.
- `evaluate(code)`: executes browser JavaScript through CDP; use browser APIs only, not Node.js APIs.
- `write_file(file_name, content, append=False, trailing_newline=True, leading_newline=False)`: overwrites by default; use `append=True` or `replace_file` for targeted edits.
- `read_file(file_name)`: reads managed files, user-supplied files, downloads, documents, and images where supported.
- `replace_file(file_name, old_str, new_str)`: exact string replacement for targeted edits.

## Excluding Defaults

```python
from browser_use import Tools

tools = Tools(exclude_actions=['search', 'evaluate'])
tools.exclude_action('screenshot')
```

Useful exclusions:

- Remove `search` when the task must stay inside a fixed web application.
- Remove `evaluate` when arbitrary page JavaScript is outside policy.
- Remove `write_file`/`replace_file`/`read_file` for tasks that must not persist local artifacts.
- Remove `screenshot` when visual capture is not allowed.
- Remove `upload_file` when file exfiltration or incorrect upload risk is unacceptable.

## JavaScript Evaluation Guidance

Use `evaluate` for custom selectors, hover/drag helpers, page structure analysis, or reading page state that indexed elements do not expose.

Safe pattern:

```javascript
(function(){
  try {
    const rows = [...document.querySelectorAll('table tr')].slice(0, 5);
    return rows.map(r => r.innerText).join('\n');
  } catch (e) {
    return 'Error: ' + e.message;
  }
})()
```

Rules:

- Use only browser APIs: `document`, `window`, DOM APIs, and web APIs.
- Do not use `fs`, `require`, `process`, shell commands, or Node.js assumptions.
- Keep output small; very large results are truncated.
- Prefer indexed `click` for shadow DOM elements when Browser Use exposes indexes.
- Do not use `evaluate` to bypass app security or user confirmation.

## Default Action Results

Default actions return `ActionResult` with combinations of:

- `extracted_content`: immediate observation for the current step.
- `long_term_memory`: concise durable summary.
- `error`: recoverable failure text.
- `metadata`: coordinates, image metadata, or action-specific details.
- `images`: image read/screenshot payloads where supported.
- `include_extracted_content_only_once`: prevents repeated memory bloat for large reads.

Treat `error` as a signal to recover, not necessarily a Python exception. Browser Use often returns expected web interaction failures as `ActionResult(error=...)` so the agent can try a different route.

## Structured Completion

`Tools(output_model=MyModel)` or agent structured-output configuration can replace the normal `done` action with a schema-backed structured completion action. Keep schema/model design in `../../llm-and-output/SKILL.md`; keep action behavior here.

## Default Action Troubleshooting

- `Element index ... not available`: page changed; refresh state, wait, search page text, or re-locate the element.
- `Cannot click on <select>`: use `dropdown_options` then `select_dropdown`.
- File input click blocked: use `upload_file`, not `click`.
- Navigation failed with `ERR_*` or `net::`: retry, check network/proxy/CDP session, or route browser setup to `../../browser-control/SKILL.md`.
- Autocomplete after `input`: wait for suggestions and click the intended suggestion instead of pressing Enter blindly.
- Long/hung action: Browser Use applies per-action timeouts; if a CDP connection is unresponsive, restart or recreate the browser session.
