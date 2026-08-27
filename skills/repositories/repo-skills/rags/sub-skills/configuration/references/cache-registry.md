# Cache Registry Reference

## Purpose

Use this when troubleshooting sidebar selection, stale agents, broken persisted
indexes, or manual cache inspection.

## Conceptual Layout

RAGs stores generated agents under a cache root like this:

```text
cache/
  agents/
    agent_ids.json
    <agent-id>/
      cache.json
      storage/
        ... LlamaIndex persisted vector index files ...
```

The exact checkout location is user-controlled; avoid hard-coding absolute
paths. The bundled inspector accepts `--cache-dir` so future agents can point it
at the active cache root.

## `agent_ids.json`

`AgentCacheRegistry.get_agent_ids()` reads `agent_ids.json` and returns the list
under the `agent_ids` key. If the file is absent, it returns an empty list. If
an ID appears in the list but its directory is missing, sidebar selection may
show a stale agent that cannot be loaded.

## Per-Agent `cache.json`

`ParamCache.save_to_disk` writes a JSON payload containing:

- `system_prompt`
- `file_names`
- `urls`
- `directory`
- `tools`
- `rag_params`
- `builder_type`
- `agent_id`

It deliberately does not serialize the live agent object or documents. On load,
RAGs reloads documents from the stored source fields, reloads the vector index
from `storage/`, reconstructs any extra tools, and rebuilds a chat engine.

## `storage/`

The `storage` directory holds the persisted LlamaIndex vector store. If it is
missing or inconsistent, loading a selected agent can fail even when
`cache.json` exists. In that case, rebuilding the agent from the original data
source is usually safer than patching index files manually.

## Safe Inspection

Run:

```bash
python sub-skills/configuration/scripts/inspect_agent_cache.py --cache-dir cache/agents
```

The helper reports registry status, listed IDs, discovered directories, missing
entries, extra directories, and whether each cache has `cache.json` and
`storage/`. It does not delete or modify files.

## Stale Cache Recovery

The public README notes that upgrades can break stored cache data structures.
When a launch or load failure appears after upgrading RAGs:

1. Inspect cache state read-only.
2. Preserve any needed user notes about data sources or agent IDs.
3. Prefer deleting the affected generated agent through the app when possible.
4. If the app cannot launch, remove or move the stale cache directory only with
   user approval.
5. Rebuild the bot from the original source data and task description.
