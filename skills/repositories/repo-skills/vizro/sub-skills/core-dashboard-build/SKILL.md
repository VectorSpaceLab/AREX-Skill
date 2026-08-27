---
name: core-dashboard-build
description: "Build, validate, run, and troubleshoot Vizro dashboards in Python
  or YAML using vizro-core models and the Vizro app wrapper."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Core Dashboard Build

Use this sub-skill when the task is to create, validate, run, deploy, or troubleshoot a Vizro dashboard at the dashboard/page/layout level.

Route elsewhere when the task is mainly about:
- Data, controls, actions, or component wiring: `../core-components-data-actions/SKILL.md`.
- Chart selection or Plotly figure code: `../charts-and-figures/SKILL.md`.
- Agent/MCP dashboard generation: `../mcp-agent-workflows/SKILL.md`.
- Repository tests/build tooling: `../repo-development-testing/SKILL.md`.

## Fast Path: Python dashboard

```python
from vizro import Vizro
import vizro.models as vm

page = vm.Page(
    title="Overview",
    components=[
        vm.Card(text="Hello Vizro"),
    ],
)

dashboard = vm.Dashboard(pages=[page], title="My dashboard")
app = Vizro().build(dashboard)  # returns the Vizro wrapper
app.run(debug=True)
```

Important: `Vizro().build()` returns the `Vizro` wrapper. Use `app.dash` for raw Dash APIs, callback maps, `index_string`, server integration, or app title checks.

## Fast Path: YAML dashboard

YAML examples load into the same Pydantic models:

```python
from pathlib import Path
import yaml
from vizro import Vizro
from vizro.models import Dashboard

config = yaml.safe_load(Path("dashboard.yaml").read_text(encoding="utf-8"))
dashboard = Dashboard(**config)
Vizro().build(dashboard).run()
```

Use `scripts/validate_vizro_dashboard.py dashboard.yaml` to parse and build without starting a server.

## Dashboard/page rules of thumb

- Build from `vm.Dashboard(pages=[...])` and `vm.Page(title=..., components=[...])` first; add data, filters, actions, and charts after the skeleton validates.
- Keep each page title unique and human-readable. The navigation layer derives behavior from pages and routes.
- Prefer documented Vizro models over raw Dash components for normal authoring; raw Dash components are useful for custom components only after model options are exhausted.
- Use Pydantic validation errors as a guide: they usually point to a wrong model field, wrong component type, or missing required nested object.
- If a page uses external assets, pass `assets_folder` into `Vizro(...)` rather than relying on the current working directory.

## Layout guidance

- Use Vizro containers/layout models for dashboard layout rather than manual Dash CSS when possible.
- Start with simple vertical page structure and introduce grids/tabs/containers only when the user asks for specific layout behavior.
- Existing e2e-flow layout knowledge in the repository favors task-driven layouts: prioritize dashboard purpose, page hierarchy, and scan order before styling details.

## Validation and smoke checks

```bash
# Installed package smoke
python scripts/probe_vizro_environment.py

# Validate a YAML or Python dashboard without running a server
python scripts/validate_vizro_dashboard.py path/to/dashboard.yaml
python scripts/validate_vizro_dashboard.py path/to/app.py
```

For repository edits, use package-local tests from `../repo-development-testing/SKILL.md`; do not start with full browser e2e unless the task actually touches browser behavior and Chrome/Chromium is available.

## Evidence anchors

- `vizro-core/src/vizro/_vizro.py`: `Vizro`, `build`, `run`, Dash app handling.
- `vizro-core/src/vizro/models/_dashboard.py`, `_page.py`: core model validation/build behavior.
- `vizro-core/examples/tutorial/app.py`: Python dashboard example.
- `vizro-core/examples/dev/yaml_version/{app.py,dashboard.yaml}`: YAML loading pattern.
- `vizro-core/docs/pages/user-guides/{layouts,run-deploy}.md` and existing `vizro-e2e-flow` dashboard/YAML/layout skills.
