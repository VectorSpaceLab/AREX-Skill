# Troubleshooting

## Import and installation

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pageindex'` | The repository is source-first and the package root is not on `PYTHONPATH`. | Use a checkout-aware environment, run from a source checkout, or install/make the dependency set importable before running bundled scripts. Then run `python scripts/check_env.py`. |
| No package version from `importlib.metadata` | The repository does not declare packaging metadata. | Treat the commit in `repo-provenance.md` as the version baseline and verify imports from source. |
| `pip check` failures after installing dependencies | Conflicting runtime packages. | Recreate a private environment with the dependency set in `configuration.md`; avoid broad optional extras unless the route needs them. |

## Model credentials and providers

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `OPENAI_API_KEY is not set` | The selected model path uses the OpenAI SDK and no key is present. | Set `OPENAI_API_KEY`, use `CHATGPT_API_KEY` as the legacy alias, or choose an offline mode such as Flash `--no-summary` / `--optimize merge`. |
| Empty or malformed model JSON replies | Provider returned empty, truncated, or non-JSON content. | Use a stable model, lower document scope, retry, and inspect whether the failing workflow is TOC detection, TOC transformation, page-number filling, or summary generation. |
| Agentic demo imports fail | Optional agent framework missing. | Install `openai-agents` only when running the agentic RAG pattern. Core `PageIndexClient` retrieval does not require it. |

## Classic PDF extraction

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| PDF path rejected | Path missing, not a file, or not `.pdf`. | Validate the file path and extension before calling the CLI or `page_index`. |
| TOC sections are out of order or page indexes are invalid | LLM-modified TOC order or hallucinated physical markers. | The code rejects reordered/modified TOC entries and nullifies invalid markers. Retry with a better model or use Flash for structure-only extraction. |
| Large sections stay too broad | Recursive splitting thresholds too high or model failed to find substructure. | Tune `--max-pages-per-node`, `--max-tokens-per-node`, and `--toc-check-pages`; consider Flash plus merge/expand optimization. |
| Slow or costly run | Classic PDF path performs multiple LLM calls. | Use Flash with `--no-summary` for first-pass structure, then selectively run summaries or optimization. |

## Flash PDF extraction

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `PDF file not found`, encrypted, or unreadable | Flash validates path, extension, PDF header, and PDFium readability. | Use a real unencrypted PDF file. Decrypt or repair the PDF before processing. |
| Empty structure | Document is very short, mostly empty/landscape, unsupported script, or extraction gate filtered the outline. | Try embedded bookmarks (`--embedded-toc` default), inspect the PDF text extraction quality, or use classic PDF extraction if model-backed reasoning is acceptable. |
| Unexpected bookmark behavior | Embedded bookmarks are classified as full, skeleton, or ignored based on density/trustworthiness. | Use `--no-embedded-toc` for pure detected structure; compare with embedded-TOC enabled output. |
| `--optimize` unexpectedly needs an API key | Full optimization expands nodes with an LLM. | Use `--optimize merge` or module CLI `--no-expand` for deterministic merge-only optimization. |

## Markdown extraction

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| A heading is missing | It was inside a fenced code block, not an ATX heading, or a bold-only heading was empty/whitespace. | Use `#`-style headings outside code blocks or non-empty `**Heading**` lines. |
| Too many tiny nodes | Markdown had dense headings and thinning was disabled. | Enable `--if-thinning yes` and tune `--thinning-threshold`. |
| Summaries trigger model calls unexpectedly | Config defaults can add summaries. | Pass `--if-add-node-summary no` and `--if-add-doc-description no` for offline structural conversion. |
| User asks for page ranges on Markdown | Markdown uses `line_num` as the location key. | Explain that retrieval ranges are line numbers for Markdown documents. |

## Workspace retrieval

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Document <id> not found` | The workspace did not load that id or the id is wrong. | Inspect `_meta.json`, list `client.documents`, and confirm the document JSON file exists. |
| `Invalid pages format` | `get_page_content` expects strings like `"5-7"`, `"3,8"`, or `"12"`. | Validate the page selector before the tool call. |
| Workspace loads but structure/page content is empty | Full document JSON is missing, corrupt, or lacks cached pages/source path. | Rebuild the workspace by indexing again or repair the document JSON. The client prints warnings on corrupt JSON. |
| Relative source paths resolve incorrectly | Workspace metadata has a relative `path`. | `PageIndexClient` resolves relative paths against the workspace directory; update the path or rely on cached `pages`. |

## Safety reminders

- Do not run live model-backed examples without the user's credentials and budget approval.
- Do not fetch entire long documents through retrieval tools; use the structure first, then tight page ranges.
- Use bundled scripts and references instead of relying on original repository docs, examples, or notebooks at runtime.
