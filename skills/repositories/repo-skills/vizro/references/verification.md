# Vizro verification guidance

Use this reference when validating changes made with the Vizro skill or when refreshing this skill.

## Fast installed-package verification

From the `skills/disco/vizro` directory:

```bash
python scripts/probe_vizro_environment.py
python scripts/inspect_vizro_schema.py --models Dashboard Page Card Graph Table Button Filter Slider Checklist Dropdown
```

With a dedicated inspection prefix:

```bash
conda run --prefix "<env-prefix>" python scripts/probe_vizro_environment.py
```

Expected checks:

- `vizro`, `vizro.models`, `vizro.plotly.express` import.
- `Vizro().build(vm.Dashboard(...))` succeeds and `.dash` is present.
- `vizro_dash_components.Cascader` and `Markdown(children=...)` instantiate.
- `vizro_ai.agents._chart_agent.chart_agent` imports, with the package deprecation warning understood.
- `vizro_mcp.server` exposes `mcp`, `create_dashboard`, and `validate_dashboard_config`.
- `vizro_experimental.chat.models.chat.Chat` and `vizro_experimental.chat.popup.add_chat_popup` import.

## Focused native tests by package

Run from the relevant package directory. Prefer narrow tests for touched behavior before broad suites.

### `vizro-core`

CPU-friendly candidates:

```bash
cd vizro-core
hatch run test-unit tests/unit/vizro/models/test_dashboard.py
hatch run test-unit tests/unit/vizro/models/test_page.py
hatch run test-unit tests/integration/test_examples.py
```

If not using Hatch, ensure the package is installed from the checkout and run equivalent `pytest` commands from `vizro-core/`.

Browser-backed candidates (requires Chrome/Chromium):

```bash
cd vizro-core
hatch run test-e2e tests/e2e/vizro/test_dom_elements/test_actions.py
```

### `vizro-mcp`

```bash
cd vizro-mcp
hatch run test-unit tests/unit/vizro_mcp/test_server.py
```

Useful for dashboard validation/server-schema changes.

### `vizro-ai`

```bash
cd vizro-ai
hatch run test-unit tests/unit/vizro-ai/agents/test_chart_agent.py
```

Do not run provider-backed examples unless credentials and network use are authorized. Remember the package is deprecated.

### `vizro-experimental`

CPU-friendly candidates:

```bash
cd vizro-experimental
hatch run test-unit tests/unit/test_component.py tests/unit/test_security.py tests/unit/popup/test_popup.py
```

Browser-backed candidates require Chrome/Chromium and the package's browser fixtures.

### `vizro-dash-components`

After TypeScript/component changes:

```bash
cd vizro-dash-components
npm install --legacy-peer-deps
npm run build
hatch run test
```

If `dash-generate-components` is not found during `npm run build`, run backend generation from an environment where `dash[dev]` is installed:

```bash
dash-generate-components ./src/ts/components vizro_dash_components -p package-info.json --ignore \.test\.
```

`hatch run test` is browser-backed; skip or mark blocked if Chrome/Chromium is unavailable.

## Static/content checks for this skill

The generated skill should contain:

- Root `SKILL.md` with a route map covering all subskills.
- Subskill `SKILL.md` files for dashboard build, components/data/actions, charts/figures, MCP workflows, deprecated AI chart agent, experimental chat popup, dash components build, and repo development/testing.
- `references/package-map.md`, `references/environment.md`, and this verification reference.
- Utility scripts under `scripts/` that run without network/provider calls.

Suggested static assertions:

```bash
find skills/disco/vizro -name SKILL.md | sort
python -m compileall -q skills/disco/vizro/scripts
python skills/disco/vizro/scripts/probe_vizro_environment.py
```

## Failure handling

- Import failures: confirm the environment installed local packages from the checkout and that `vizro-dash-components` generated wrappers exist or a wheel was installed.
- `Markdown` constructor failure: use `children=...`; there is no `markdown_text` keyword in this snapshot.
- `Vizro` app probe failure: remember `Vizro().build()` returns a Vizro wrapper. Access raw Dash state at `.dash`.
- Browser test failures: first confirm Chrome/Chromium availability and driver compatibility before changing application code.
- Provider/LLM failures: confirm the task actually required live provider calls; prefer mocked/BYO callbacks for routine repository verification.
