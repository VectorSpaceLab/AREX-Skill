# Memory workflows

## Prove local memory without touching user state

Use the bundled script first when you need a safe confirmation that the local memory stack can save, search, and delete.

```bash
python sub-skills/memory/scripts/memory_smoke.py
python sub-skills/memory/scripts/memory_smoke.py --json
python sub-skills/memory/scripts/memory_smoke.py --db-path ./scratch-memory.db
```

Default behavior uses a temporary database and removes it after the run. Passing `--db-path` intentionally writes to that database and leaves it for inspection.

Manual equivalent:

```python
import asyncio
from tempfile import TemporaryDirectory
from pathlib import Path
from headroom.memory import Memory

async def main():
    with TemporaryDirectory() as tmp:
        memory = Memory(db_path=Path(tmp) / "memory.db")
        try:
            mid = await memory.save("User prefers pytest", user_id="demo", importance=0.8)
            hits = await memory.search("test framework", user_id="demo", top_k=3)
            assert any(hit.id == mid or "pytest" in hit.content.lower() for hit in hits)
            assert await memory.delete(mid)
        finally:
            await memory.close()

asyncio.run(main())
```

If the smoke fails before saving, check optional dependencies and local embedder availability before changing app code.

## Add local memory to a synchronous OpenAI-compatible client

```python
from openai import OpenAI
from headroom.memory import with_memory

client = with_memory(
    OpenAI(),
    user_id="alice",
    db_path="./app-memory.db",
    top_k=5,
    session_id="session-001",
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "I prefer short answers and Python."}],
)
```

Use this when you want automatic inline extraction and injection. It is best with sync clients and normal chat-completion loops.

Safe operation checklist:

- Choose a stable `user_id` that does not leak private identity if logs are shared.
- Set `db_path` explicitly in applications.
- Keep `top_k` small unless the user asks for a broad recall.
- Do not save passwords, tokens, or secrets; if the model suggests doing so, prevent the tool call or delete the memory.

## Use explicit memory tools in an LLM loop

Use `with_memory_tools` when you want the model to decide when to save/search/update/delete through function calling.

```python
from openai import OpenAI
from headroom.memory import LocalBackend, LocalBackendConfig, with_memory_tools

backend = LocalBackend(LocalBackendConfig(db_path="./memory.db", embedder_backend="onnx"))
client = with_memory_tools(
    OpenAI(),
    backend=backend,
    user_id="alice",
    optimized=True,
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Remember: use Ruff before pytest."}],
)

if hasattr(response, "_memory_tool_results"):
    for tool_call_id, result in response._memory_tool_results.items():
        print(tool_call_id, result["message"])
```

Use optimized mode when the backend supports pre-extracted `facts`, `extracted_entities`, and `extracted_relationships`. Use standard mode when you want the smallest tool schema.

## Move from local to Qdrant/Neo4j-backed memory

1. First prove behavior locally with a temp DB.
2. Install the memory stack dependencies and start Qdrant + Neo4j services.
3. Pass service URLs through environment variables or runtime config; never hardcode credentials.
4. Switch construction only after connectivity is known:

```python
from headroom.memory import Memory

memory = Memory(
    backend="qdrant-neo4j",
    qdrant_url="https://your-qdrant-host.example",
    neo4j_uri="neo4j://localhost:7687",
)
```

5. Export the local database before migration if the existing memories are user state:

```bash
headroom memory export --db-path ./memory.db --output memory-backup.json
```

## Inspect and clean a memory database

Start with read-only commands:

```bash
headroom memory stats --db-path ./memory.db
headroom memory list --db-path ./memory.db --limit 20
headroom memory list --db-path ./memory.db --search "database" --scope USER
headroom memory show --db-path ./memory.db <id> --json
```

Then use previews and backups before changes:

```bash
headroom memory export --db-path ./memory.db --output before-cleanup.json
headroom memory prune --db-path ./memory.db --older-than 30d --dry-run
headroom memory prune --db-path ./memory.db --older-than 30d --force
```

For supersession issues, repair only the known bad edge:

```bash
headroom memory repair-supersession --db-path ./memory.db <old-id> <new-id>
headroom memory repair-supersession --db-path ./memory.db <old-id> <new-id> --apply
```

## Configure MCP for CCR retrieval

Use `headroom mcp install` when an MCP-compatible agent should get Headroom's `headroom_compress`, `headroom_retrieve`, and `headroom_stats` tools.

```bash
headroom mcp install --agent claude
headroom mcp status
```

If proxy-backed retrieval is required:

```bash
# terminal 1
headroom proxy

# terminal 2
headroom mcp install --proxy-url http://127.0.0.1:8787 --force
# restart the MCP host after install
```

Decision tree:

- Agent does not see tools: run `headroom mcp status`, reinstall for the right agent, then restart the host.
- Tools appear as `mcp__headroom__headroom_retrieve`: normal namespace display.
- `headroom_retrieve` says content missing or expired: re-run the original command or re-read the source file rather than retrying the stale hash.
- Status says configured but proxy unavailable: start or repair the proxy through `proxy-wrap`; the memory sub-skill only owns the MCP registration and `--proxy-url` value.

## Run MCP server manually for debugging

```bash
headroom mcp serve --debug
headroom mcp serve --proxy-url http://127.0.0.1:9000 --debug
headroom mcp serve --transport http --host 127.0.0.1 --port 8788 --path /mcp
```

Use manual serve only for debugging or custom MCP hosts. Normal use lets the MCP host spawn the stdio server from its config.

## Use persistent memory MCP tools directly

For native memory save/search MCP tools, use the dedicated memory MCP module rather than `headroom mcp serve`:

```bash
python -m headroom.memory.mcp_server --db .headroom/memory.db --user alice
```

This exposes `memory_search` and `memory_save`. It is useful for hosts that should share Headroom's local memory database across sessions. Keep `--db` explicit when multiple projects or agents are involved.

## Recover Codex state after interrupted wrapping

Start with a dry discovery prompt:

```bash
headroom recover codex
```

If it finds sources, it prints target, source homes, and backup behavior before prompting. Apply only after the target looks correct:

```bash
headroom recover codex --yes
```

For manual recovery from a known temp home:

```bash
headroom recover codex --source <temporary-codex-home> --target <active-codex-home>
```

After recovery:

1. Open Codex and run the normal resume/list command for all work directories.
2. Check that sessions and config are intact.
3. Keep recovery backups until confirmed.
4. If a previous temp home was already deleted, only durable history records may remain; full transcripts cannot be restored without retained rollout files.

## Learn failure guardrails from agent transcripts

```bash
headroom learn                      # dry run for current project / auto agent
headroom learn --agent codex --all  # dry run across Codex projects
headroom learn --apply              # write generated recommendations
```

Use this after repeated agent failures such as wrong paths, missing modules, or stubborn retry loops. The command needs either an API key-backed model, a supported local CLI backend, or an explicit `--model`.

Safe defaults:

- Dry run first.
- Use `--project` to avoid scanning all discovered projects unless requested.
- Use `--target CLAUDE.md` only when the team wants shared rules; default Claude output is personal/local.
- Use `--workers 1` for serial scanning if the machine is I/O constrained.

## Learn output verbosity

```bash
headroom learn --verbosity
headroom learn --verbosity --apply
```

Use this when the user wants Headroom to infer how terse model outputs should be from observed behavior. It currently uses Claude Code transcript signals.

What `--apply` does:

- Writes the learned profile under the Headroom workspace.
- Seeds the output-savings baseline used for counterfactual output token savings.
- Attempts to hot-enable output shaping on a running local proxy.
- If no proxy is reachable, prints the `HEADROOM_OUTPUT_SHAPER=1` guidance for the next proxy start or wrap.

The actual proxy setup and wrap behavior belongs to `proxy-wrap`; this workflow only covers the learning command and what it writes.
