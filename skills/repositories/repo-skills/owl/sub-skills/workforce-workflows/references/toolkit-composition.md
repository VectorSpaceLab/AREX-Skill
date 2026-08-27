# Toolkit Composition

The canonical Workforce example creates three workers with intentionally
separate responsibilities. The exact list can vary by provider example, but
the boundaries below are stable source evidence.

| Worker | Typical tools | Use for |
|---|---|---|
| Web Agent | DuckDuckGo/Wikipedia search, `DocumentProcessingToolkit.extract_document_content`, BrowserToolkit tools | Search, discover authoritative URLs, browse dynamic pages, and combine page extraction with browser actions. |
| Document Processing Agent | DocumentProcessingToolkit, ImageAnalysisToolkit where available, CodeExecutionToolkit, FileToolkit | Local/remote documents, images, files, and code-assisted extraction. |
| Reasoning Coding Agent | CodeExecutionToolkit, ExcelToolkit, DocumentProcessingToolkit | Structured reasoning, Python calculations, spreadsheet processing, and local document support; source descriptions say it cannot search the internet. |

The example also creates `ExcelToolkit`, `SearchToolkit`, `BrowserToolkit`,
`FileToolkit`, and `CodeExecutionToolkit(sandbox="subprocess", verbose=True)`.
`BrowserToolkit` receives separate browsing and planning models and defaults to
`headless=False` in the examples; use `headless=True` on a remote/headless
host only after Playwright/browser prerequisites are prepared.

## Composition rules

- Wrap bound toolkit methods with `FunctionTool` when passing a single method
  to `ChatAgent`; expand a toolkit's `get_tools()` list when it exposes several
  operations.
- Give each worker a description that states what it can and cannot do. The
  Workforce task agent and coordinator agent decompose and assign work; they do
  not replace specialist tools.
- Use a multimodal model for image or video analysis. Text-only tool calling
  is not equivalent to vision support.
- Keep code and terminal tools sandboxed and constrain file output paths. A
  task that writes a file still needs a final existence/content check.
- Do not ask the web worker to rely only on a search snippet. The source prompt
  recommends search for discovery, then authoritative page extraction or
  browser interaction, and reporting visited URLs.
- For local documents, use [document-processing](../../document-processing/SKILL.md)
  for format-specific prerequisites instead of adding every optional service.

## Minimal shape

```python
web_agent = ChatAgent(
    "Search and verify authoritative sources.",
    model=web_model,
    tools=[FunctionTool(search.search_duckduckgo), *browser.get_tools()],
)
workforce = Workforce("Workforce", task_agent=task_agent,
                     coordinator_agent=coordinator_agent)
workforce.add_single_agent_worker("Web worker", worker=web_agent)
result = workforce.process_task(Task(content=question))
```

Treat this as an assembly pattern, not a copy-and-run script. Model creation,
keys, browser setup, and toolkit versions must be validated in the target
environment.
