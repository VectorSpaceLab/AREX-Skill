# Troubleshooting

## Import or install problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` when importing `agentscope.agent` or `agentscope.tool` | Editable install is stale, or the environment is not the one you meant to inspect | Run `../../../scripts/check_env.py`, then reinstall the selected extras in the target environment |
| `pip check` fails after an install | Mixed extras or partially upgraded dependencies | Reinstall the environment cleanly if possible; do not mutate a shared user environment without permission |
| `agentscope.tool` imports but a particular provider/tool fails later | The provider or workspace extra is missing | Switch to the matching sub-skill and install the missing optional dependency |

## Tool and permission issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| A file tool refuses to touch a path | The path is protected by the built-in safety rules | Use an unprotected working directory or update the permission context instead of bypassing the guard |
| A task tool or MCP tool is missing from the toolkit | The tool group was not activated or the MCP client was not passed in | Rebuild the `Toolkit` with the intended tools / groups / MCP clients |
| `ToolCallBlock` input does not match the tool schema | The tool schema and the message payload diverged | Re-check the tool's JSON schema and the stringified input produced by the model |

## Skill loading issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Toolkit(..., skills_or_loaders=...)` shows no skills | The path does not contain a valid `SKILL.md` | Fix the directory name or frontmatter and try again |
| A nested skill is missing | `scan_subdir` is still false | Set `scan_subdir=True` only when you really want recursive discovery |
| Skill instructions look stale | The underlying `SKILL.md` changed but the loader cache has not refreshed | Recreate the loader or re-read the files after a fresh mtime |

## Conversation and event issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `reply_stream()` seems to stop before the final answer appears | You are only watching the streaming deltas, not the optional final message | Use `yield_final_msg=True` or collect the end-of-stream `Msg` explicitly |
| A structured-output turn fails near the end | The model did not satisfy the schema or the grace-iters budget | Tighten the schema, simplify the prompt, or increase the relevant config |
| Interruption or confirmation events appear unexpectedly | The workflow or permission setup allows pauses | Handle the event explicitly in the agent loop rather than assuming a single-shot reply |

## When to escalate elsewhere

- Provider-specific credential or model-name issues → `provider-connectors`
- Retrieval/memory or vector-store mismatches → `rag-memory`
- Service deployment, storage, or channel issues → `service-platform`
- Workspace backend or archive/seed issues → `workspace-sandboxes`
