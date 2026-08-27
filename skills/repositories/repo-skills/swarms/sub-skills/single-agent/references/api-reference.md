# Single-agent API reference

This reference condenses the verified public surface that most single-agent tasks need.

## `Agent` constructor highlights

Verified installed signature facts:

- `agent_name='swarm-worker-01'`
- `agent_description='An autonomous agent that can perform tasks and learn from experience powered by Swarms'`
- `model_name='gpt-5.4'`
- `max_loops=1`
- `interactive=False`
- `autosave=False`
- `streaming_on=False`
- `stream=False`
- `prompt_caching=False`
- `context_compression=True`
- `persistent_memory=False`
- `skills_dir=None`
- `marketplace_prompt_id=None`
- `mcp_url=None`, `mcp_urls=None`, `mcp_config=None`, `mcp_configs=None`
- `selected_tools='all'`
- `reasoning_effort='medium'`
- `output_type='str-all-except-first'`

Only a subset of the constructor is usually user-facing. The most common knobs are the agent name, model, loop count, tools, skills, memory, streaming, prompt caching, and marketplace prompt id.

### Commonly used fields

| Field | Purpose | Notes |
| --- | --- | --- |
| `agent_name` | Stable identifier and memory key | Use a descriptive, unique name. |
| `system_prompt` | Base instruction block | Can be empty, but should be explicit for production use. |
| `model_name` | LiteLLM model string | Defaults to `gpt-5.4`. |
| `max_loops` | Number of reasoning loops | `"auto"` enables autonomous planning/execution. |
| `tools` / `tools_list_dictionary` | Local tool integration | Tool conversion lives in `tools-mcp`. |
| `skills_dir` | Folder of `SKILL.md` files | Each skill is a subdirectory with YAML frontmatter. |
| `persistent_memory` | Persist `MEMORY.md` across runs | Default is `False` in the installed package. |
| `context_compression` | Summarize long sessions | Useful for long autonomous runs. |
| `prompt_caching` / `cache_config` | Provider-side prompt caching | Provider support varies. |
| `marketplace_prompt_id` | Fetch a prompt from the marketplace | Requires `SWARMS_API_KEY`. |
| `mcp_url` / `mcp_urls` | Connect MCP tools | See `tools-mcp` for the full transport story. |

## `Agent.run`

Signature summary:

```python
run(task=None, img=None, imgs=None, correct_answer=None, streaming_callback=None, n=1, *args, **kwargs)
```

Important behavior:

- If `task` is missing and `interactive=False`, the call raises a `ValueError`.
- If `max_loops == "auto"`, the agent uses its autonomous planning/execution loop.
- If `n > 1`, the agent returns a list of runs.
- If `skills_dir` exists, skills are loaded before execution.
- Live provider execution may fail on invalid keys, unsupported model parameters, or missing network access.

## `Agent.run_stream`

- Yields token chunks one by one.
- Keeps the underlying run in a background thread.
- Good for UI or CLI streaming checks when a full response is not required.

## Support objects

### `SkillsManager`

- `prompt_for_task(task=None)` loads every skill when `task` is omitted or only relevant skills when a task is supplied.
- `load_metadata(skills_dir=None)` scans subdirectories for `SKILL.md` files with YAML frontmatter.
- `load_full_skill(skill_name)` returns the body below the frontmatter for one loaded skill.

### `Conversation`

- `add(role, content)` appends to history.
- `return_history_as_string()` gives a printable transcript.
- `compact(summary=...)` collapses long history into a summary.
- `save()` and `load()` persist conversation state.

### `Artifact`

- Tracks file contents and versions.
- `create(initial_content)`, `edit(new_content)`, `save()`, `load()`, `export_to_json(file_path)`.
- File type is inferred from `file_path` when omitted.

### `AgentMarketplaceHandler`

- `fetch(...)` retrieves a prompt by id or name.
- `load_prompt(...)` appends the prompt to the owning agent.
- `publish(...)` sends a prompt and metadata back to the marketplace.
- Requires `SWARMS_API_KEY`.

## Practical checks

- If you only need to prove the package works, start with a constructor/import check and avoid live model calls.
- If skills do not appear, confirm the directory shape is `skills_dir/<skill-name>/SKILL.md`.
- If memory is missing, confirm `WORKSPACE_DIR` and the agent name are stable.
- If a provider call fails, compare the model family, prompt-caching settings, and reasoning parameters against the provider’s accepted payload.
