---
name: mcp-agent-workflows
description: "Use and maintain Vizro-MCP FastMCP server workflows for dashboard
  creation, validation, schemas, and PyCafe sharing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MCP Agent Workflows

Use this sub-skill when the task involves `vizro-mcp`, MCP server setup, agent-assisted dashboard generation, dashboard validation, schema extraction, PyCafe links, or repository changes under `vizro-mcp/`.

Route elsewhere when the task is mainly about:
- Hand-writing a dashboard without MCP: `../core-dashboard-build/SKILL.md`.
- Chart semantics inside a generated dashboard: `../charts-and-figures/SKILL.md`.
- Deprecated `vizro-ai`: `../legacy-ai-chart-agent/SKILL.md`.

## Package facts

- Import package: `vizro_mcp`.
- Main evidence file: `vizro-mcp/src/vizro_mcp/server.py`.
- The installed `vizro_mcp.server` exposes `mcp`, `create_dashboard`, `validate_dashboard_config`, schema/result models, and PyCafe helper functions in this snapshot.
- `vizro-mcp` depends on `mcp`, `httpx`, `click`, `pandas[html,parquet,excel]`, `pydantic-settings`, and `vizro`.

## Safe first moves

For a user asking to use MCP with Vizro:

1. Explain that Vizro-MCP is the maintained agent-assistance route in this monorepo.
2. Check installed package importability before launching a server:

   ```bash
   python - <<'PY'
   import vizro_mcp.server as s
   print(hasattr(s, 'mcp'), hasattr(s, 'create_dashboard'), hasattr(s, 'validate_dashboard_config'))
   PY
   ```

3. Inspect `vizro-mcp/README.md` for current server/CLI setup expected by the repository.
4. Use validation helpers/schema output before generating or sharing external artifacts.

## Dashboard generation/validation principles

- Treat generated dashboard code/config as untrusted until validated by Vizro models and, when feasible, built with `Vizro().build()`.
- Validate data paths and external URLs before embedding them in dashboards.
- Avoid writing files outside a user-approved output directory.
- Prefer deterministic local validation over agent/model calls when debugging generated code.
- If PyCafe sharing is requested, confirm whether network upload/link creation is allowed.

## Schema work

When the task asks for schema/model JSON or LLM-facing dashboard instructions:

- Use `vizro_mcp.server` schema helpers and schema models as the source of truth.
- Cross-check with `vizro-core` model fields using `scripts/inspect_vizro_schema.py` when changes involve core model definitions.
- Keep schema output free of local absolute paths and secrets.

## Repository edits

For changes under `vizro-mcp/`:

```bash
cd vizro-mcp
hatch run lint
hatch run test-unit tests/unit/vizro_mcp/test_server.py
```

If Hatch is unavailable, use the prepared installed-package environment and run focused `pytest` from `vizro-mcp/`, but preserve the package working directory.

## Common failures

- `validate_dashboard_config` errors usually mean the generated dashboard does not match current `vizro.models` schemas. Inspect the model fields and fix the config, not the validator.
- Missing Excel/parquet/html dependencies: install/verify `pandas[html,parquet,excel]` extras.
- MCP server launch issues: separate import errors from transport/server configuration errors.
- PyCafe URL issues: check network permission and the helper in `tools/pycafe/create_pycafe_links_comments.py`.

## Evidence anchors

- `vizro-mcp/README.md`
- `vizro-mcp/src/vizro_mcp/server.py`
- `vizro-mcp/src/vizro_mcp/_schemas/schemas.py`
- `vizro-mcp/tests/unit/vizro_mcp/test_server.py`
- `tools/pycafe/create_pycafe_links_comments.py`
