---
name: repo-development-testing
description: "Work safely in the Vizro monorepo: package layout, Hatch commands,
  build steps, focused tests, changelog, and backend-classified verification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Repo Development and Testing

Use this sub-skill whenever the task changes repository code, docs, tests, package metadata, build scripts, generated assets, or developer tooling in the Vizro monorepo.

Also load the feature sub-skill that owns the changed behavior.

## Monorepo package map

- `vizro-core/`: main `vizro` framework.
- `vizro-ai/`: deprecated chart agent package.
- `vizro-mcp/`: MCP server package.
- `vizro-experimental/`: incubating experimental features.
- `vizro-dash-components/`: TypeScript/React Dash components plus generated Python package.
- `vizro-e2e-flow/`: Claude Code plugin/reference skills; do not run Hatch commands there.

## Working-directory rule

Run Hatch from the package directory, not the monorepo root:

```bash
cd vizro-core
hatch run lint
hatch run test-unit
```

Common Hatch commands across packages:

```bash
hatch run python -c "import package"
hatch run pypath
hatch run lint
hatch run test-unit
hatch run docs:serve
hatch run changelog:add
```

Do not assume every package defines every script; check `hatch.toml`/`pyproject.toml` for the package you are editing.

## Focused verification matrix

| Changed area | First focused checks |
| --- | --- |
| Dashboard/page/model behavior in `vizro-core` | `cd vizro-core && hatch run test-unit tests/unit/vizro/models/test_dashboard.py` plus the touched model tests. |
| Core examples/YAML/docs | `cd vizro-core && hatch run test-unit tests/integration/test_examples.py` where feasible; validate specific YAML/Python example with `scripts/validate_vizro_dashboard.py`. |
| Actions/controls/tables | Focus unit tests for the touched model/action plus browser e2e only if browser backend is available and behavior is DOM/callback-specific. |
| `vizro-mcp` server/schema | `cd vizro-mcp && hatch run test-unit tests/unit/vizro_mcp/test_server.py`. |
| `vizro-ai` chart agent | `cd vizro-ai && hatch run test-unit tests/unit/vizro-ai/agents/test_chart_agent.py`; avoid provider-backed live calls. |
| `vizro-experimental` chat | `cd vizro-experimental && hatch run test-unit tests/unit/test_component.py tests/unit/test_security.py tests/unit/popup/test_popup.py`. |
| `vizro-dash-components` TypeScript/components | `cd vizro-dash-components && npm install --legacy-peer-deps && npm run build`; browser tests require Chrome/Chromium. |

## Browser backend gate

Before running e2e/browser tests:

```bash
command -v google-chrome || command -v chromium || command -v chromium-browser
```

If no browser exists, do not claim browser tests passed. Use CPU/import/build checks and report the browser gate as blocked.

## Generated-file rules

- `vizro-dash-components/vizro_dash_components/` files are generated. Edit `src/ts` and regenerate.
- Generated docs/templates should be updated through the repo's scripts (for example `vizro-core/tools/generate_templates.py`) rather than by hand when possible.
- If running npm generation dirties lockfiles unintentionally, inspect the diff and revert unrelated lockfile churn.

## Changelog and lint

For PR-quality work, run package lint and add a changelog fragment when the repository workflow requires it:

```bash
cd <package>
hatch run lint
hatch run changelog:add
```

If the user's task is only skill construction or analysis, do not create product changelog fragments.

## Environment probe

Use the bundled skill probe to confirm installed-package health:

```bash
python skills/disco/vizro/scripts/probe_vizro_environment.py
```

Or with the prepared prefix:

```bash
conda run --prefix "<env-prefix>" python skills/disco/vizro/scripts/probe_vizro_environment.py
```

## Troubleshooting

- Import mismatch: ensure the intended package was installed from the local checkout, not a stale PyPI version.
- Hatch missing: either install Hatch as the repo's development dependency or run equivalent `python -m pytest` commands inside a prepared environment.
- Browser failure: check Chrome/Chromium and driver compatibility before changing app code.
- LLM/provider failure: confirm credentials and authorization; otherwise mock/BYO callbacks.
- `vizro-dash-components` build failure: run `npm install --legacy-peer-deps`, then ensure `dash-generate-components` is on PATH.

## Evidence anchors

- Root/package `AGENTS.md` and `CLAUDE.md` files.
- Package `hatch.toml` and `pyproject.toml` files.
- `references/environment.md` and `references/verification.md` in this skill.
