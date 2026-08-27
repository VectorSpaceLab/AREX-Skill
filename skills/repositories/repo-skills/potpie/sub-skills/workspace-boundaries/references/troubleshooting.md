# Workspace boundary troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No active pot` or no selected workspace | Setup has not created/selected a pot, or the session lost its default. | Run `potpie pot list`, then `potpie pot use <name-or-id>` or create one with `potpie pot create <name>`. |
| Current repo is not linked | The repo was never registered, or a repo default points elsewhere. | Run `potpie pot linked`, `potpie pot default show .`, and `potpie source list`; register with `potpie source add repo .` if needed. |
| `source add repo .` resolves unexpectedly | The checkout has no remote, multiple remotes, or a relative path that is not stable across sessions. | Inspect git remotes and use an explicit remote URL or absolute path when durable identity matters. |
| A graph read is empty after source registration | Registration records metadata only; it does not ingest or create graph records. | Confirm pot/source state, then route to graph read/write workflows or ingestion/nudge paths as appropriate. |
| `pot default show` differs from the active pot | Repo default and active shell selection are independent. | Decide whether the task should follow the repo default or current active pot, then set or clear the default explicitly. |
| `pot reset` was suggested as a fix | Reset is destructive and may remove workspace graph state. | Do not run it as a generic recovery step. Ask for explicit user confirmation and preserve any export/backup guidance first. |
| Source removal breaks later commands | Downstream graph/ledger operations refer to the removed source id. | Re-register the source or update affected records/queries to the intended source id. |

## Safe inspection sequence

When workspace state is unclear, use read-only commands first:

```bash
potpie pot list
potpie pot info
potpie pot linked
potpie pot default show .
potpie source list
```

Then choose the narrowest mutating command:

- `potpie pot use <pot>` only changes selection.
- `potpie pot default set . <pot>` changes repo default behavior.
- `potpie source add repo <repo>` registers a source.
- `potpie pot create <name> --repo <repo>` creates a workspace and optionally registers a source.

## Repo identity pitfalls

- `.` means the current shell directory; it is convenient but can be ambiguous in scripts.
- `current` is a shorthand that still depends on checkout discovery.
- Remote URLs are better for long-lived cross-machine identity.
- Local-only paths are valid when the workflow is intentionally local, but future agents should not assume that path exists.

## No-scan rule

Do not tell the user that `source add repo` scanned, parsed, embedded, or ingested the repository unless another command or service actually did that work. Treat source registration as a boundary marker that later graph/ledger/ingestion paths can use.
