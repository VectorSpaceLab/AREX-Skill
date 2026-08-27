# Troubleshooting

## Backend availability issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `initialize()` fails on a container backend | The host runtime is missing the backend prerequisite | Check the backend matrix and fall back to `LocalWorkspace` for a smoke test |
| `get_backend()` raises before initialization | The workspace was not initialized yet | Await `initialize()` first |
| A backend works on one host but not another | The runtime prerequisite is host-specific | Compare the host requirements in `backend-matrix.md` |

## Skill and archive issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `add_skill()` rejects the directory | The directory does not contain a valid `SKILL.md` | Fix the frontmatter and try again |
| `add_skill_archive()` fails to expand the archive | The archive is malformed, too large, or attempts path traversal | Rebuild the archive and keep the payload within the documented limit |
| A skill appears duplicated after manual edits | The `.skills` index no longer matches the directory contents | Re-run `list_skills()` so the workspace reconciles the index |

## MCP issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `add_mcp()` raises a name conflict | The MCP name must be unique | Rename one of the clients before adding it |
| A stateful MCP disappears after startup | The backend could not reconnect it | Check the client config and the host service before editing the workspace code |
| `remove_mcp()` leaves stale state | The workspace was already out of sync | Reconcile the `.mcp` file by re-running the lifecycle methods rather than editing it manually |

## Safe next steps

- Use `scripts/local_workspace_smoke.py` to validate the local backend first.
- If the smoke test passes but a remote backend fails, the issue is probably backend-specific rather than a skill-content problem.
- If the issue is really the tool layer or agent permissions, switch to `agent-core`.
