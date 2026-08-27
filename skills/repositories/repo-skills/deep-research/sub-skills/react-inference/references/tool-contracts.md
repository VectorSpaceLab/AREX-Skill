# ReAct Tool Contracts

The system prompt tells the model to emit one tool call as JSON inside `<tool_call>...</tool_call>`. The runtime then returns tool output to the model inside `<tool_response>...</tool_response>`. A final answer must be enclosed in `<answer>...</answer>`.

## Common Tool-Call Envelope

Non-Python tools should look like:

```xml
<tool_call>
{"name": "search", "arguments": {"query": ["example query"]}}
</tool_call>
```

Runtime rules:

- The content between `<tool_call>` and `</tool_call>` is parsed with JSON5 for non-Python tools.
- The parsed object should contain `name` and `arguments`.
- Unknown names return `Error: Tool <name> not found`.
- Invalid JSON returns `Error: Tool call is not a valid JSON. Tool call must contain a valid "name" and "arguments" field.`
- The model call uses stop strings for `<tool_response>`, so an assistant should not invent its own tool responses.

## `search`

Purpose: perform Google web searches through Serper and return top organic snippets.

Signature exposed to the model:

```json
{"name": "search", "arguments": {"query": ["query one", "query two"]}}
```

Contract:

| Item | Detail |
|---|---|
| Required argument | `query`: array of strings. The implementation also accepts a single string, but the prompt requests an array. |
| Credential | `SERPER_KEY_ID`. |
| Endpoint behavior | Uses Serper `/search`; Chinese queries are sent with China/Chinese locale hints, other queries with United States/English hints. |
| Result format | Text headed by `A Google search for '<query>' found N results`, then numbered web results with title, link, optional date, source, and snippet. Multiple queries are joined with `=======`. |
| Retry behavior | Up to five connection attempts per query. |
| Common failures | Missing/invalid key, Serper quota/rate limits, no `organic` results, overly specific query, network timeout. |

Operational advice: ask the model or user to batch complementary queries in one call when possible. If results are empty, broaden the query before retrying many times.

## `google_scholar`

Purpose: retrieve academic search results through Serper Scholar, plus some web-style metadata.

Signature:

```json
{"name": "google_scholar", "arguments": {"query": ["paper or topic query"]}}
```

Contract:

| Item | Detail |
|---|---|
| Required argument | `query`: array of strings; implementation also tolerates a single string. |
| Credential | `SERPER_KEY_ID`. |
| Endpoint behavior | Uses Serper `/scholar`. Multiple queries run with up to three worker threads. |
| Result format | Text headed by `A Google scholar for '<query>' found N results`, then numbered scholar results with title, pdfUrl when present, publication info, year, cited-by count, and snippet. |
| Retry behavior | Up to five connection attempts per query. |
| Common failures | Missing Serper key, no scholar results, rate limits, query too narrow, no available PDF link. |

Operational advice: use this for academic-source discovery, not final benchmark judging.

## `visit`

Purpose: read one or more webpages and summarize content relevant to a goal.

Signature:

```json
{"name": "visit", "arguments": {"url": ["https://example.test/page"], "goal": "specific information to extract"}}
```

Contract:

| Item | Detail |
|---|---|
| Required arguments | `url`: string or array of strings; `goal`: string. |
| Read credential | `JINA_API_KEYS` for the Jina reader request. |
| Summary credentials | `API_KEY`, `API_BASE`, `SUMMARY_MODEL_NAME` for the OpenAI-compatible summarizer used after page retrieval. |
| Time and length controls | `VISIT_SERVER_TIMEOUT` default is `200`; retrieved content is token-truncated before summarization; array visits stop giving full attempts after about 900 seconds. |
| Result format | For each URL: useful-information preamble, `Evidence in page`, and `Summary`. Multiple URLs are joined with `=======`. |
| Retry behavior | Jina read attempts repeat; summary attempts retry and then progressively truncate content. |
| Common failures | Missing Jina key, inaccessible page, summary model returning non-JSON, missing `API_BASE`/`API_KEY`, page too long, provider timeout. |

Operational advice: supply a narrow `goal`; broad goals make summaries less useful and more expensive.

## `PythonInterpreter`

Purpose: execute Python code in a SandboxFusion endpoint and return stdout/stderr.

Prompt-required call shape:

```xml
<tool_call>
{"name": "PythonInterpreter", "arguments": {}}
<code>
print(2 + 2)
</code>
</tool_call>
```

Runtime behavior:

- The ReAct loop treats any tool-call content containing the word `python` specially.
- It extracts code between `<code>` and `</code>` and passes only that raw code to the Python tool.
- The tool samples one endpoint from comma-separated `SANDBOX_FUSION_ENDPOINT` values for each attempt.
- Default per-run timeout is about `50` seconds.
- It returns `stdout:`, `stderr:`, timeout messages, or `Finished execution.` when there is no output.

Common failures:

- `SANDBOX_FUSION_ENDPOINT` is missing or empty, causing endpoint selection failure.
- Endpoint is unreachable or overloaded.
- Code omitted `print(...)`, so the tool returns no useful stdout.
- Code block tags are malformed, causing `[Python Interpreter Error]: Formatting error.` from the ReAct loop.
- User expected local filesystem access; SandboxFusion execution is remote/sandboxed and should not be assumed to see local files.

Operational advice: tell the model to print concise results and avoid long-running code. For deterministic setup checks, validate endpoints outside expensive rollouts first.

## `parse_file`

Purpose: parse uploaded local files and return extracted file content or summaries.

Signature:

```json
{"name": "parse_file", "arguments": {"files": ["report.pdf", "table.xlsx"]}}
```

Contract:

| Item | Detail |
|---|---|
| Required argument | `files`: array of file names. |
| File root | The dispatcher resolves names under `./eval_data/file_corpus` relative to the inference working directory. |
| Supported types from prompt | PDF, DOCX, PPTX, TXT, CSV, XLSX, DOC, ZIP, MP4, MP3 and common media/audio variants. |
| Credentials | Dashscope variables for rich document/video parsing; optional IDP variables when IDP mode is enabled. Simple text files may parse without the full service path depending on parser behavior. |
| Result format | List-like content sections beginning with file names, token counts, and extracted content; compressed if content is too long. |
| Common failures | File not present under `file_corpus`, absolute or traversal paths, parser dependencies missing, Dashscope/IDP credentials absent, unsupported media type, very large archive/media file. |

Operational advice: validate file names with `scripts/validate_deepresearch_dataset.py --file-corpus` before a rollout. Do not expose local absolute file paths in questions; use corpus-relative names only.

## Answer Contract

The system prompt requires the final response to enclose the entire definitive answer in `<answer></answer>` tags. The runner extracts prediction text by splitting on those tags. If the model writes a good answer without tags, downstream output still becomes `No answer found.` or a format-error termination.

When diagnosing no-answer outputs, inspect the last assistant message in `messages`: it may contain an untagged answer, a malformed tag, a final tool call that exceeded limits, or a token-limit prompt response that did not obey the format.
