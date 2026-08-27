# SDK and Adapter Troubleshooting

## Import and package naming

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: open_chatchat` | Wrong spelling | Use `open_chatcaht` as inspected in this repository. |
| `ModuleNotFoundError: open_chatcaht` | SDK package not installed | Install the project SDK package or install from source package; verify with `python -c "import open_chatcaht"`. |
| SDK distribution version looks like `0.0.0` | Current editable build metadata does not match source pyproject package name/version | Treat import/signature checks as authoritative for this checkout; refresh if upstream packaging changes. |
| `langchain_chatchat` import fails | Server distribution dependencies missing or wrong environment | Install/verify `langchain-chatchat`; run root environment probe. |

## Connection and base URL

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ConnectError` or connection refused | Chatchat API is not running or base URL is wrong | Start `chatchat start --api`; pass `base_url="http://host:7861/"`; verify API docs/root redirect. |
| SDK calls hit wrong server | Ambient `CHATCHAT_API_BASE` overrides or default points to localhost | Pass `base_url` explicitly in scripts and tests. |
| Timeouts on chat/RAG | Provider/model call is slow or hung | Increase SDK timeout only after provider health is confirmed; inspect Chatchat and provider logs. |

## Streaming generator issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Code expects a dict but gets a generator | SDK chat/RAG/OpenAI methods stream responses | Iterate the generator and collect chunks; set non-streaming route options only when supported. |
| Generator yields `{'code': 500, 'msg': ...}` | SDK stream wrapper caught connection/JSON/timeout error | Treat it as an error object; inspect `msg` and route to setup/API troubleshooting. |
| JSON parse errors while streaming | SSE chunks may arrive split or include comments | Use SDK helper or an SSE parser rather than raw `json.loads` on arbitrary chunks. |

## KB mutation risks

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Accidental KB deletion/update | SDK call targeted production KB | Use explicit test KB names; ask before calling delete/update/recreate methods; backup `CHATCHAT_ROOT`. |
| Upload succeeds but search fails | Docs were not vectorized or embedding provider failed | Check `upload_kb_docs(to_vector_store=True)`, provider model, and direct `search_kb_docs`. |
| Download writes unexpected path | `download_kb_doc_file` defaults `file_path` to `file_name` | Pass a safe output path explicitly. |

## Adapter failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ChatPlatformAI` returns provider errors | `api_base`, model name, or provider credentials are wrong | Verify provider with API sub-skill; pass explicit model/base/key. |
| `PlatformToolsRunnable` construction errors | Missing `AgentExecutor`, callback, or required agent state | Use SDK/API tool calls for simple use; only construct runnable in a LangChain agent context. |
| MCP conversion rejects content | Unsupported embedded resource/image content | Convert only text prompt messages or handle unsupported content before calling conversion helpers. |

## Safe first live SDK checks

1. `client = ChatChat(base_url="http://127.0.0.1:7861/")`
2. `client.server.get_server_configs()`
3. `client.tool.list()`
4. Only after those work, try KB upload/search or chat calls.

If step 2 fails, fix API startup/base URL first. If step 3 fails, inspect tool registry/config. If chat fails after 2 and 3 pass, inspect provider/model settings.
