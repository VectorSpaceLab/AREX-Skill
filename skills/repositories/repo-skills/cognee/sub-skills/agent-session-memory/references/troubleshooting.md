# Agent and Session Memory Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `SessionPreconditionError` says no default user or no `main_dataset` | Session APIs were used before Cognee initialized a user/dataset. | Add or remember data first, run inside a dataset context, or pass an explicit `session_id` and user. |
| Session recall misses recent context | `CACHING` is disabled or the selected cache backend is unavailable. | Enable/configure caching in [configuration-backends](../../configuration-backends/SKILL.md) or search the graph scope instead. |
| `agent_memory` rejects the decorated function | The target is not async. | Convert the function to `async def` before decorating. |
| `memory_query_from_method` fails | The named method parameter does not exist or is blank. | Use an existing parameter name or switch to `memory_query_fixed`. |
| Decorator config rejects boolean/string fields | A decorator argument has the wrong type. | Pass booleans for boolean switches and non-empty strings for query/session names. |
| Feedback cannot be attached | `qa_id` is missing/wrong or the QA entry is not in that session. | Use the `entry_id` returned by the QA write and the matching `session_id`. |
| Agent creation leaves no dataset grants | The caller was not authorized to read a requested dataset, so creation should fail before grants. | Have the acting user gain dataset access first, then create the agent. |
| Different agents see each other's memory | The same dataset/session id is reused across agents. | Create separate agent session names and dataset scopes for isolation. |

## Safe validation helper

Use the bundled payload checker before writing memory entries:

```bash
python scripts/check_agent_memory_payloads.py --help
python scripts/check_agent_memory_payloads.py --type qa --payload '{"question":"q","answer":"a"}' --pretty
```

The checker validates Pydantic payload schemas only; it does not write to a cache or graph.
