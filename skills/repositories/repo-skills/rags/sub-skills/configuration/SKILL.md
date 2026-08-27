---
name: configuration
description: "Use this RAGs sub-skill to inspect, edit, update, delete, and
  troubleshoot generated RAG agent configuration and cache state."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RAGs Configuration

Use this sub-skill when a RAGs agent already exists and the task is to inspect
or change its settings, understand persisted cache state, recover from stale
cache issues, or delete an agent safely.

## Read This When

- The user is on the RAG Config page or mentions `Update Agent`, `Delete Agent`,
  `agent_id`, `top_k`, `chunk_size`, `embed_model`, `llm`, or additional tools.
- The sidebar shows an agent but loading, updating, or deleting it fails.
- The task involves `AgentCacheRegistry`, `ParamCache`, `agent_ids.json`,
  `cache.json`, or vector-index `storage`.
- The app was upgraded and old cache files appear to break launch.

For initial bot construction, read [`../builder/SKILL.md`](../builder/SKILL.md).
For asking questions to an existing bot, read [`../chat/SKILL.md`](../chat/SKILL.md).

## Core Workflow

1. Confirm an agent is selected. The config page only exposes editable controls
   when the current state has an `agent_builder` and cache.
2. Inspect current fields: agent ID, system prompt, loaded data summary,
   summarization flag, additional tools, `top_k`, `chunk_size`, embed model,
   and LLM.
3. Before editing cache files directly, run the read-only inspector:

   ```bash
   python sub-skills/configuration/scripts/inspect_agent_cache.py --cache-dir cache/agents
   ```

4. Use the app's `Update Agent` path for normal changes. It deletes the old
   cache entry, updates selected fields, reconstructs the agent, and saves the
   new cache.
5. Use the app's delete route for unwanted agents. Manual deletion is a last
   resort for stale or corrupt cache directories.

Read [`references/configuration.md`](references/configuration.md) for field
semantics and update/delete workflows. Read
[`references/cache-registry.md`](references/cache-registry.md) before editing or
inspecting persisted cache. Read
[`references/troubleshooting.md`](references/troubleshooting.md) for known
failure modes.

## Important Operating Facts

- The cache root is conceptually `cache/agents` relative to a RAGs checkout.
- `AgentCacheRegistry.get_agent_ids()` returns an empty list when
  `agent_ids.json` is absent.
- `ParamCache.save_to_disk` requires a vector index and writes both serialized
  cache metadata and vector-index storage.
- `RAGAgentBuilder.update_agent` deletes the old cache for the current agent ID,
  sets the requested fields, calls `set_rag_params`, updates tools when
  provided, and then calls `create_agent`.
- Additional tools are currently limited to `web_search`.

## Safety Boundaries

The bundled cache inspector is read-only. Do not delete cache directories or
rewrite `agent_ids.json` unless the user explicitly asks for destructive
recovery and understands that generated agents may need to be rebuilt.
