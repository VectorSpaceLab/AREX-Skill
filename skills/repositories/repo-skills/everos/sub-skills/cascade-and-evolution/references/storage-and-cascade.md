# Storage and Cascade Reference

## Memory root layout

```text
<memory-root>/
  <app_id>/<project_id>/
    users/<user_id>/
      user.md
      episodes/episode-<YYYY-MM-DD>.md
      .atomic_facts/atomic_fact-<YYYY-MM-DD>.md
      .foresights/foresight-<YYYY-MM-DD>.md
    agents/<agent_id>/
      .cases/agent_case-<YYYY-MM-DD>.md
      skills/skill_<name>/SKILL.md
    knowledge/
  .index/sqlite/
    system.db
    ome.db
    ome.aps.db
    ome.db.lock
  .index/lancedb/
  ome.toml
  .tmp/
```

The reserved id `default` materializes as `default_app/default_project`.

## Storage roles

| Layer | Holds | Operator rule |
|---|---|---|
| Markdown | Business memory content and frontmatter | Source of truth; editable. |
| SQLite | `md_change_state`, buffers, memcell rows, OME state, clusters/audit | Do not delete blindly; buffers may not be in Markdown yet. |
| LanceDB | Vector/BM25/scalar business indexes | Rebuildable from Markdown. |

## Cascade daemon

The cascade daemon runs in-process with the server. It has:

1. Watcher loop for filesystem events.
2. Scanner loop for missed events.
3. Worker loop that claims `md_change_state` rows and upserts/deletes LanceDB rows.

Startup recovers orphan `processing` rows. Health exposes a `cascade` block when the full lifespan is running.

## CLI commands

### Status

```bash
everos cascade status --root <root>
```

Look for `pending`, retryable/permanent failures, and `lag`.

### Sync

```bash
everos cascade sync --root <root>
everos cascade sync --root <root> users/u1/episodes/episode-2026-01-01.md
```

Without a path it drains existing pending work. With a path it force-enqueues that Markdown file if it matches a registered cascade kind.

### Fix

```bash
everos cascade fix --root <root>
everos cascade fix --apply --root <root>
```

`fix` lists failed rows. `--apply` requeues retryable failures and drains once. Permanent failures require editing the bad Markdown and re-saving.

### Rebuild

```bash
everos cascade rebuild --root <root>
```

Stop the server first. Rebuild drops business LanceDB tables, recreates schema/indexes, resets cascade queue state, and re-scans Markdown. It preserves unprocessed buffers because it does not delete the whole `.index/` tree.
