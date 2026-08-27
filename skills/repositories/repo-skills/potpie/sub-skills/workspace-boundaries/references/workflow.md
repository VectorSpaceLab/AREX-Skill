# Workspace boundary workflow reference

Potpie separates **pots** (workspace/tenant containers) from **sources** (registered repositories or external systems). A repo can be registered and linked without scanning or ingesting content.

## Command matrix

| Goal | Command family | Notes |
| --- | --- | --- |
| List available pots | `potpie pot list` | Start here when the active workspace is unclear. |
| Inspect current pot | `potpie pot info` | Shows the selected pot and related metadata. |
| Create a pot | `potpie pot create <name>` | Add `--repo <path-or-remote>` to register a repo source during creation. |
| Switch pot | `potpie pot use <name-or-id>` | Changes the active workspace for later commands. |
| Inspect linked repos | `potpie pot linked` | Useful before graph reads/writes that depend on repo scope. |
| Manage repo default | `potpie pot default show|set|clear` | Prefer this over relying on the current shell directory. |
| Rename/archive/reset | `potpie pot rename|archive|reset` | `reset` is destructive; require explicit user intent. |
| Register a repo source | `potpie source add repo <path-or-remote>` | Registration is metadata; it is not a scan or ingest. |
| List sources | `potpie source list` | Shows registered sources for the active pot. |
| Check source health | `potpie source status <source>` | Use before debugging graph emptiness. |
| Remove source | `potpie source remove <source>` | Can affect later graph/ledger routing; confirm intent. |

## Common flows

### First repo in a new workspace

```bash
potpie setup --dry-run --repo .
potpie setup --repo .
potpie pot linked
potpie source list
```

If setup is too broad for the task, use the narrower pot/source commands instead:

```bash
potpie pot create my-project --repo .
potpie pot use my-project
potpie pot default set . my-project
```

### Register without changing the default

```bash
potpie pot create audit-space --repo . --no-default
potpie pot linked
potpie pot default show .
```

Use this when the user wants a temporary or comparison workspace.

### Add a remote/provider source later

```bash
potpie source add repo https://github.com/org/repo.git
potpie source list
potpie source status https://github.com/org/repo.git
```

Provider authentication still belongs to `auth-integrations`; source registration only records the source relationship.

## Repo identity rules

- `.` and `current` should resolve through the current checkout when a git remote or absolute path can identify the repository.
- A stable remote URL is usually a better long-lived identity than a temporary relative path.
- If a checkout has multiple remotes, inspect and choose deliberately instead of accepting an ambiguous default.
- If a repo has no remote, Potpie can still register a local path, but future sessions may need the same path or an explicit `pot default` entry.

## Boundary with graph operations

Pot/source commands define *where* graph reads and writes apply. They do not by themselves prove that graph records exist.

Before diagnosing an empty graph:

1. Confirm the active pot: `potpie pot info`.
2. Confirm linked repo/default: `potpie pot linked` and `potpie pot default show .`.
3. Confirm registered source: `potpie source list` and `potpie source status ...`.
4. Then route to `graph-read` or `graph-write`.
