# Troubleshooting

This reference collects the cross-cutting Quivr failure modes that matter most
for routing and support.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Brain.from_files` or `Brain.afrom_files` fails on a non-empty input list | The live snapshot still mishandles `ProcessedDocument` inside `process_files()` | Use `SimpleTxtProcessor.process_file(...).chunks` plus `Brain.afrom_langchain_documents(...)` until the repository fixes the bug |
| `process_file(...)` seems to return a single object instead of a list | `ProcessorBase.process_file()` returns a `ProcessedDocument` wrapper | Read `.chunks` for the actual `Document` list |
| `Brain.ask(...)` complains about the event loop or the call signature | `Brain.ask` is a synchronous wrapper that still needs `run_id` | Use `Brain.aask(...)` / `Brain.ask_streaming(...)` from async code, or call `ask` only from a plain synchronous script with a `run_id` |
| `Brain.save(...)` says the embedder or vector store cannot be serialized | The save path only supports FAISS plus OpenAI embeddings | Rebuild the brain with a serializable embedder/vector store before saving |
| Search works but citations or source labels look wrong | Custom `Document` metadata is missing `original_file_name` | Preserve `original_file_name` in document metadata or use processor-generated chunks |
| The text splitter produces too many or too few chunks | The splitter settings are not tuned for the document size | Adjust `SplitterConfig(chunk_size=..., chunk_overlap=...)` |
| `TAVILY_API_KEY` errors appear when enabling web search | The web-search tool is active but no Tavily key is set | Set `TAVILY_API_KEY` and include `web search` in `WorkflowConfig.available_tools` |
| Provider warnings mention a missing API key | The selected provider key is absent | Set the provider-specific key name from `configuration.md` or use a fake/local model for smoke tests |
| `transformers` warns that PyTorch is not found | The runtime does not have `torch` installed | This is non-blocking for the bundled CPU smoke path; install PyTorch only if you need real model execution |
| `Langfuse client is disabled` appears during import | No `LANGFUSE_PUBLIC_KEY` was provided | This is expected for offline smoke and does not block the bundled scripts |
| `TIKA_SERVER_URL` requests fail | The optional Tika service is not running | Start a Tika server or stay on the plain-text path |
| Optional parser imports fail for `unstructured` or MegaParse processors | Those backends are not part of the minimum CPU smoke set | Treat them as optional backend work, not as a core-skill regression |
| Old examples call `Brain.ask(question)` without `run_id` | Example drift | Treat the old snippet as stale and update it to the current signature |
| Repo tests fail on old signatures or old defaults | The test suite still contains stale expectations against the live API | Prefer the current runtime signatures and bundled smoke scripts; record the failing test as repo drift rather than a skill error |

## Fast check list

1. Confirm the user is on the core ingestion or QA path.
2. Check whether the issue is about `chunks`, `run_id`, or serialization.
3. If the answer is yes, route to the matching sub-skill.
4. If the issue depends on an optional backend, confirm that the backend is actually installed or running before promising success.
