# Repo Provenance

```json
{
  "schema": "disco.repo-provenance.v1",
  "skill_id": "vizro",
  "source_repo": "mckinsey/vizro",
  "source_commit": "99634b8e837d371f0d25c53692278b39236594e6",
  "source_branch": "main",
  "package_versions": {
    "vizro": "0.1.61.dev0",
    "vizro-dash-components": "0.3.1.dev0",
    "vizro-ai": "0.4.3.dev0",
    "vizro-mcp": "0.1.5.dev0",
    "vizro-experimental": "0.1.1.dev0"
  },
  "dirty_state_at_construction": "Runtime skill output was untracked under skills/. Temporary generated build artifacts for vizro-dash-components were produced as ignored package build outputs; tracked source/package-lock changes were restored before verification.",
  "evidence_categories": [
    "package source",
    "public docs",
    "examples",
    "tests",
    "tooling scripts",
    "existing repo-local e2e-flow skills",
    "installed package inspection"
  ]
}
```

## Evidence scope

Major relative evidence paths consulted:

- `README.md`, `pyproject.toml`, root/package `AGENTS.md` and `CLAUDE.md` files.
- `vizro-core/src/vizro/`, especially `_vizro.py`, `models/`, `actions/`, `figures/`, `managers/`, and `plotly/express.py`.
- `vizro-core/docs/pages/user-guides/` for dashboard run/deploy, layouts, data, actions, filters, selectors, custom charts/components, tables, and graph/table actions.
- `vizro-core/examples/tutorial/`, `vizro-core/examples/tutorial-custom-actions/`, `vizro-core/examples/dev/yaml_version/`, and `vizro-core/examples/visual-vocabulary/`.
- `vizro-ai/src/vizro_ai/`, `vizro-ai/docs/pages/API-reference/vizro-ai.md`, `vizro-ai/examples/example.py`, and chart-agent tests.
- `vizro-mcp/src/vizro_mcp/`, `vizro-mcp/README.md`, and `vizro-mcp/tests/unit/vizro_mcp/test_server.py`.
- `vizro-experimental/src/vizro_experimental/`, chat docs/examples, and chat/popup/security tests.
- `vizro-dash-components/src/ts/`, package docs/examples/tests, and generated wrapper import probes.
- `vizro-e2e-flow/skills/` reference skills for dashboard build/design/layout/chart/action/YAML workflows.
- `tools/scan_yaml_for_risky_text.py`, `tools/pycafe/create_pycafe_links_comments.py`, and `vizro-core/tools/generate_templates.py`.

## Freshness check

Refresh this skill when:

- Any Vizro package version changes materially.
- `vizro-core` model signatures, `Vizro().build()` behavior, or `vizro.plotly.express` wrappers change.
- `vizro-mcp` server tools/resources/schemas are renamed or reorganized.
- `vizro-ai` deprecation policy or chart-agent surface changes.
- `vizro-experimental` chat/popup APIs graduate, move, or change optional dependency boundaries.
- `vizro-dash-components` exported components, props, generation pipeline, or package build scripts change.
- Browser/e2e backend requirements change enough that currently optional blocked tests become mandatory gates.
