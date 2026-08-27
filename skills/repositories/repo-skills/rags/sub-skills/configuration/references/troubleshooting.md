# Configuration Troubleshooting

## No `Update Agent` Button

**Symptom:** the config page shows fields or a message, but no update button.

**Likely cause:** no agent has been created, or the selected cache has no live
agent object.

**Fix:** create an agent through the builder route first. If the sidebar shows
an old ID, inspect cache consistency before assuming the agent exists.

## `Agent builder is None`

**Symptom:** update or delete raises `ValueError("Agent builder is None...")`.

**Likely cause:** Streamlit session state lost or failed to reconstruct the
builder from the selected cache.

**Fix:** refresh the app, reselect the agent, and inspect `cache/agents`. If the
cache is corrupt or from an older version, rebuild the agent.

## Duplicate Agent ID

**Symptom:** saving a new cache raises `ValueError("Agent id ... already exists.")`.

**Likely cause:** `AgentCacheRegistry._add_agent_id_to_directory` rejects IDs
already listed in `agent_ids.json`.

**Fix:** choose a new ID or intentionally delete the old agent first. Do not
manually edit `agent_ids.json` unless recovering a corrupt registry with user
approval.

## Sidebar Shows an ID That Will Not Load

**Symptom:** the sidebar lists an agent, but selection fails or the config page
cannot reconstruct it.

**Likely cause:** `agent_ids.json` lists an ID whose directory, `cache.json`, or
`storage/` is missing or stale.

**Fix:** run the cache inspector, compare listed IDs with actual directories,
and rebuild or delete the stale entry.

## Missing `storage/`

**Symptom:** `cache.json` exists but loading the vector index fails.

**Likely cause:** `ParamCache.save_to_disk` persists the vector index under
`storage/`; without it the cache cannot reconstruct the chat engine.

**Fix:** rebuild the agent from the original data. Avoid fabricating storage
files manually.

## Unknown Additional Tool

**Symptom:** updating tools appears to work, but later construction fails with
`Tool <name> not recognized`.

**Likely cause:** current tool resolution only recognizes `web_search`.

**Fix:** remove unknown tool names. If `web_search` is desired, ensure the
`metaphor_key` secret exists and rebuild.

## Upgrade Breaks Existing Agents

**Symptom:** app launch or selected-agent loading fails after upgrading RAGs.

**Likely cause:** the stored cache data structure may have changed.

**Fix:** inspect cache, preserve needed source/task information, then delete or
move stale cache entries with approval and rebuild from source data.
