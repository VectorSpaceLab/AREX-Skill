# Lifecycle and Resource Management

## Purpose

Read this when you need the workspace API shape, the initialization order, or the safe way to seed skills and MCPs.

## Verified core methods

| Method | Purpose |
| --- | --- |
| `initialize()` | Provision the backend, restore or seed MCPs, seed skills, and mark the workspace alive. |
| `close()` | Close stateful MCP sessions and mark the workspace inactive. |
| `reset()` | Remove skills, sessions, data, and MCP persistence for a clean slate. |
| `get_backend()` | Return the active backend object; raises if the workspace has not been initialized. |
| `list_tools()` | Return the built-in file / shell tools for the active backend. |
| `list_skills()` | Return the indexed skills currently available in the workspace. |
| `list_mcps()` | Return the registered MCP clients. |
| `add_skill()` | Copy one local skill directory into the workspace and update the index. |
| `add_skill_archive()` | Expand a ZIP / TAR / TAR.GZ skill archive and install the contained skill. |
| `remove_skill()` | Remove a skill by its agent-facing name. |
| `add_mcp()` | Register an MCP client and persist it. |
| `remove_mcp()` | Remove an MCP client and disconnect it if needed. |
| `offload_context()` | Persist conversation context to `sessions/<session_id>/context.jsonl`. |
| `offload_tool_result()` | Persist tool output to `sessions/<session_id>/tool_result-<id>.txt`. |

## Initialization order

1. Construct the workspace with the intended backend and seed lists.
2. Await `initialize()` before calling `get_backend()`, `list_tools()`, or mutation methods.
3. Use `list_tools()` / `list_skills()` / `list_mcps()` to confirm what the agent can see.
4. Add or remove skills and MCPs through the methods, not by editing workspace files directly.
5. Call `close()` when you are done with the backend session.

## Skill seeding notes

- Local skill directories must contain a valid `SKILL.md` with `name` and `description` frontmatter.
- `add_skill_archive()` is the safe archive-import path because it validates path traversal and extraction size.
- `LocalWorkspace` deduplicates skills by the `SKILL.md` content hash and handles name conflicts with suffixes.

## MCP notes

- Stateful MCPs are connected on initialization and disconnected on close or remove.
- MCP names must be unique because they become part of the model-facing tool name.
- The `.mcp` file is the persisted registry used on restart.

## Offload notes

- `offload_context()` and `offload_tool_result()` write into the workspace's `sessions/` tree.
- Inline base64 data blocks are offloaded into `data/` so JSONL stays manageable.
- Do not move the workspace root between turns if you want offloaded context and memory to remain discoverable.
