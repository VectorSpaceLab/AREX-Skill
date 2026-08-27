---
name: plugin-box-skills
description: "Work with LangBot Plugin Runtime connector and handler, sibling
  SDK boundaries, Box sandbox runtime, native and stdio MCP tools, skill CRUD,
  and in-repo skill QA assets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Plugin Runtime, Box, and Skills

Use this sub-skill when a task involves plugins, the `langbot-plugin` SDK
boundary, Plugin Runtime connection/debugging, Box sandbox sessions, native
agent tools, stdio MCP hosting, skill CRUD/storage, or the repository's in-repo
agent-skill assets.

## Read First

- [references/plugin-runtime.md](references/plugin-runtime.md) for LangBot-side
  connector/handler responsibilities and SDK boundary rules.
- [references/box-runtime-and-skills.md](references/box-runtime-and-skills.md)
  for Box service/connector, sandbox sessions, native tools, stdio MCP, and
  skill CRUD/storage.
- [references/langbot-skills-assets.md](references/langbot-skills-assets.md) for
  the in-repo `skills/` catalog and `lbs` QA tooling.
- [references/troubleshooting.md](references/troubleshooting.md) for runtime
  disconnects, Box backend errors, skill visibility, and SDK drift.

## Key Rules

- Shared plugin component APIs, message/event entities, action protocols,
  `lbp rt`, and `lbp box` live in the sibling SDK package, not in LangBot main.
- After installing a local SDK into LangBot's environment, use
  `uv run --no-sync ...` for verification or `uv` may restore the pinned SDK.
- Box-enabled tools and stdio MCP hosting require Box readiness; UI/API skill
  listings may remain visible when Box is disabled, but edit/execute paths are
  limited.
- Do not confuse external MCP servers LangBot connects to with LangBot's own
  `/mcp` server; API route details belong to `api-mcp-web`.

## Focused Checks

```bash
python scripts/select_langbot_checks.py plugin-box
uv run pytest tests/unit_tests/plugin/test_handler_actions.py tests/unit_tests/plugin/test_connector_methods.py -q --tb=short
uv run pytest tests/unit_tests/box/test_box_service.py tests/unit_tests/box/test_box_connector.py -q --tb=short
cd skills && bin/lbs validate
```

Run real Box integration tests only when Docker/Podman and socket permissions
are available and the task touches real sandbox lifecycle behavior.
