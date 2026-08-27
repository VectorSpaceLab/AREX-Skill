# Python SDK And CLI Troubleshooting

## Client Construction

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: base_url is required` | Current Python client requires an explicit base URL | Pass `base_url="http://localhost:8080"` for a local server or the correct deployed API URL. |
| Connection refused | Server not running or wrong port | Run a health check against the intended server; do not assume local `8080` is active. |
| 401/403 | Missing/invalid API key | Pass `api_key` or `--api-key` from a secret source; mask it in logs. |
| Requests hang | Timeout too high or network/proxy issue | Set `timeout`/`--timeout`; verify URL path and proxy environment. |

## Project And Context

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Search misses recently added data | Different `org_id`, `project_id`, metadata context, memory type, or async semantic ingestion | Reuse the same project and metadata; list episodic memory first; check semantic memory config if semantic results are missing. |
| API says project not found | Project was not created or context typo | Use `get_or_create_project` or CLI `projects get-or-create`; keep org/project IDs exact. |
| Cross-user leakage risk | Missing or inconsistent user/session metadata | Add explicit `user_id`, `agent_id`, `group_id`, and/or `session_id` in `Project.memory(metadata=...)`. |

## Filters

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Filter parser error near `==` | MemMachine filter grammar uses single `=` | Rewrite to `metadata.category = 'travel'`. |
| Empty result with filter | Wrong field prefix or metadata key | Try a simple unfiltered search, then add one predicate. User metadata can be written as `metadata.key` or handled with legacy `filter_dict` depending on call path. |
| Complex `OR` rejected by legacy filter | `filter_dict` supports simple equality only | Use `filter="owner = alice OR owner = bob"` instead. |

## CLI Command Shape

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `unrecognized arguments: --base-url` | Global flags placed after subcommands in some shells/examples | Put `--base-url`, `--api-key`, `--timeout`, and `--max-retries` immediately after `mem-cli`. |
| Missing project context | `--org-id`/`--project-id` omitted | Add both flags to `projects` and `memory` commands. |
| JSON parse error | Bad shell quoting for `--set-metadata` or `--extra-metadata` | Use valid JSON object syntax and shell-appropriate quotes. |
| Delete command removed wrong target | Confused episodic and semantic IDs | Use `delete-episodic` only for episodic IDs and `delete-semantic` only for semantic IDs; ask before deleting. |

## Closed Client Or Session Errors

If a method says the client is closed, construct a new `MemMachineClient` or
avoid calling methods after a context-manager block exits. Always close clients
after use in long-running applications to release HTTP connections.

## LangGraph Tool Issues

- If `memmachine_client.langgraph` imports but the graph runtime cannot load
  tools, install the LangGraph/LangChain dependency expected by the application.
- Tool helper calls still need MemMachine server URL, project context, and
  user/agent/session metadata.
- Treat tool outputs as dictionaries wrapping SDK results; inspect the installed
  version before writing strict assertions against nested keys.

## Safe Debug Checklist

1. `python -c "from memmachine_client import MemMachineClient; print(MemMachineClient)"`
2. `mem-cli --help`
3. `mem-cli --base-url "$URL" health`
4. `mem-cli --base-url "$URL" projects get --org-id "$ORG" --project-id "$PROJECT"`
5. Run one simple add/search with non-secret test content only after writes are
   approved.
