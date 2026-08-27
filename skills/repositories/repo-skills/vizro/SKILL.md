---
name: vizro
description: "Use Vizro to build, validate, debug, extend, and maintain
  dashboards across vizro-core, Vizro-MCP, deprecated Vizro-AI, experimental
  chat, and Vizro Dash Components."
disable-model-invocation: true
metadata:
  disco-role: operating
  source-repo: mckinsey/vizro
  source-commit: 99634b8e837d371f0d25c53692278b39236594e6
license: Apache 2.0
---

# Vizro

Use this skill when a task involves the Vizro monorepo or the installed Vizro packages: dashboard authoring, model/YAML validation, charts/tables/layouts/actions, MCP-assisted dashboard generation, the deprecated `vizro-ai` chart agent, experimental chat/popup components, or `vizro-dash-components` custom Dash components.

## Start Here

1. Read `references/repo-provenance.md` to confirm the source snapshot, evidence scope, and freshness limits.
2. Read `references/package-map.md` to identify the relevant package, public API surface, and known version-specific facts.
3. Read `references/environment.md` before installing packages, building `vizro-dash-components`, running tests, using browser-backed examples, or touching provider-backed LLM features.
4. Run `python scripts/probe_vizro_environment.py` in the target environment for a quick installed-package smoke check.
5. Use the route map below. Each sub-skill owns task-specific workflows and near references.
6. When modifying this repository, also route to `sub-skills/repo-development-testing/SKILL.md` for package-specific commands, backend-classified tests, and AGENTS constraints.

## Route Map

| User task | Use sub-skill | Why |
| --- | --- | --- |
| Build/run a Vizro dashboard in Python or YAML; validate `Dashboard`/`Page`/layout basics | `sub-skills/core-dashboard-build/SKILL.md` | Owns `Vizro().build()`, `Vizro().run()`, dashboard/page models, Python/YAML authoring, layout-first debug patterns. |
| Add or debug cards, graphs, tables, filters, selectors, data sources, custom components, or actions | `sub-skills/core-components-data-actions/SKILL.md` | Owns Vizro model composition, `data_manager`, action wiring, controls, table/grid behavior, and validation failures. |
| Choose or author charts/figures/tables with Plotly/Vizro conventions | `sub-skills/charts-and-figures/SKILL.md` | Owns `vizro.plotly.express`, custom chart callables, visual-vocabulary guidance, and figure model pitfalls. |
| Use or change Vizro-MCP agent/server workflows | `sub-skills/mcp-agent-workflows/SKILL.md` | Owns FastMCP server tools/resources, dashboard creation/validation helpers, schema extraction, and PyCafe workflows. |
| Inspect or maintain the deprecated `vizro-ai` chart agent | `sub-skills/legacy-ai-chart-agent/SKILL.md` | Owns `chart_agent`, response models, safeguard behavior, and deprecation-safe routing. |
| Use or modify `vizro-experimental` chat component or floating popup | `sub-skills/experimental-chat-popup/SKILL.md` | Owns `Chat`, `add_chat_popup`, lazy agent helpers, BYO callback mode, and security constraints. |
| Use/maintain `vizro-dash-components` Cascader/Markdown components or generated wrappers | `sub-skills/dash-components-build/SKILL.md` | Owns TypeScript source-of-truth, npm/webpack/dash-generate-components pipeline, props, and browser-test constraints. |
| Change repository code, docs, tests, build config, or package metadata | `sub-skills/repo-development-testing/SKILL.md` | Owns monorepo layout, Hatch commands, package-local test commands, changelog, and backend-classified verification. |

## Public Package Facts

- `vizro-core` installs the public distribution `vizro`. Public Python examples typically use:

  ```python
  import vizro.models as vm
  from vizro import Vizro

  dashboard = vm.Dashboard(pages=[vm.Page(title="Home", components=[vm.Card(text="Hello")])])
  app = Vizro().build(dashboard)   # returns the Vizro wrapper, not the raw Dash app
  app.run()
  ```

  The underlying Dash app is `app.dash` after build.
- `vizro.plotly.express` provides Vizro-oriented wrappers around Plotly Express; use it when authoring standard Vizro charts unless the task requires custom Plotly code.
- `vizro-mcp` is the preferred maintained agent-assistance path for new AI/dashboard workflows.
- `vizro-ai` is deprecated in this checkout. Maintain existing chart-agent behavior when requested, but do not recommend it for greenfield workflows when Vizro-MCP/e2e-flow is a better fit.
- `vizro-experimental` APIs may change or graduate into `vizro-core`; state that caveat in user-facing solutions.
- `vizro-dash-components` source of truth is TypeScript/React under `src/ts`. Python files and JS bundles under `vizro_dash_components/` are generated; do not hand-edit them.

## Safety Defaults

- Do not run live LLM provider calls unless the user explicitly supplies/authorizes credentials and network use. Prefer import, schema, or BYO callback checks.
- Do not require browser-backed `dash_duo`/Selenium/e2e tests on hosts without Chrome/Chromium. Treat them as optional backend-specific gates and document the missing backend.
- Do not run full monorepo test suites first. Start with package-local focused tests for the touched behavior; then broaden if needed.
- Do not edit generated `vizro_dash_components/*.py` or JS bundles directly. Edit TypeScript in `vizro-dash-components/src/ts` and regenerate.
- For repo edits, obey package-local `AGENTS.md`/`CLAUDE.md`: Hatch commands run from the specific package directory; `vizro-e2e-flow` is a Claude plugin and its guide says no Hatch commands.

## Bundled Helpers

- `scripts/probe_vizro_environment.py` checks imports and small CPU-only smoke behavior across Vizro packages.
- `scripts/inspect_vizro_schema.py` summarizes public Vizro model fields/schemas for dashboard-writing tasks.
- `scripts/validate_vizro_dashboard.py` validates a small Python or YAML dashboard path when the installed package and PyYAML are available.

## Common First Moves

- User wants a dashboard: route to `core-dashboard-build`, then to `charts-and-figures` and `core-components-data-actions` as components/charts/actions/data appear.
- User wants AI-generated or agent-validated dashboards: route to `mcp-agent-workflows`; only use `legacy-ai-chart-agent` if the task explicitly mentions `vizro-ai` or existing chart-agent code.
- User wants chat in a dashboard: route to `experimental-chat-popup`; prefer BYO `generate_response` for credential-free examples.
- User touches custom Dash components: route to `dash-components-build` and `repo-development-testing`.
- User touches repository code: load the relevant feature subskill plus `repo-development-testing`, then run focused tests with the package-local working directory.
