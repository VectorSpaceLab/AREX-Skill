# Vizro package map

Source snapshot: `mckinsey/vizro` commit `99634b8e837d371f0d25c53692278b39236594e6`.

## Package boundaries

| Directory | Distribution/imports | Primary role | Important caveats |
| --- | --- | --- | --- |
| `vizro-core/` | dist `vizro`, import `vizro` | Main Vizro dashboard framework: models, app wrapper, assets, data/action/model managers, Plotly wrappers. | `Vizro().build(dashboard)` returns the `Vizro` wrapper; use `.dash` for the Dash app. |
| `vizro-mcp/` | dist `vizro-mcp`, import `vizro_mcp` | FastMCP server for agent-assisted dashboard creation, validation, schemas, and PyCafe links. | Preferred maintained agent workflow over deprecated `vizro-ai`. |
| `vizro-ai/` | dist `vizro-ai`, import `vizro_ai` | Deprecated chart agent and response models. | `vizro_ai.__init__` emits a deprecation warning; no top-level `VizroAI` class is exported in this snapshot. |
| `vizro-experimental/` | dist/import `vizro_experimental` | Incubating features, especially chat component and floating popup. | APIs may change; popup agent helpers are lazily imported and may require provider dependencies/credentials. |
| `vizro-dash-components/` | dist/import `vizro_dash_components` | Custom Dash components used by Vizro and usable in pure Dash apps. | TypeScript under `src/ts` is source of truth; Python wrappers and bundles are generated. |
| `vizro-e2e-flow/` | Claude plugin, not normal Vizro package | Reference skills for dashboard design/build/chart/layout/action/YAML workflows. | Useful evidence; do not assume Hatch commands there. |

## Core public APIs

Typical imports:

```python
from vizro import Vizro
import vizro.models as vm
import vizro.plotly.express as px
```

Minimal dashboard:

```python
dashboard = vm.Dashboard(
    pages=[
        vm.Page(
            title="Home",
            components=[vm.Card(text="Hello Vizro")],
        )
    ],
)
app = Vizro().build(dashboard)
# app is a Vizro wrapper; app.dash is the Dash object.
```

Common model families are exposed from `vizro.models`; inspect `vizro-core/src/vizro/models/__init__.py` or run `scripts/inspect_vizro_schema.py` for live field information.

## Chart and table APIs

- Prefer `vizro.plotly.express` wrappers for standard charts in Vizro dashboards.
- Use `vm.Graph(figure=...)` for Plotly figures/charts and table/grid models for tabular views.
- Use custom chart callables only when wrappers/Plotly Express do not cover the needed figure.
- Visual-vocabulary evidence lives in `vizro-core/examples/visual-vocabulary/README.md` and `vizro-e2e-flow/skills/selecting-vizro-charts/references/chart-best-practices.md`.

## Data, actions, and controls

- `vizro.managers.data_manager` backs registered/accessed datasets.
- Actions are under `vizro.actions`; graph/table action behavior is documented under `vizro-core/docs/pages/user-guides/graph-table-actions.md` and `actions.md`.
- Filters/selectors are model-backed controls, not raw Dash callbacks in normal Vizro authoring.

## Vizro-MCP APIs

`vizro_mcp.server` imports successfully in the verified environment and exposes useful public names including:

- `mcp` / `FastMCP` server object
- `create_dashboard`
- `validate_dashboard_config`
- schema/result models such as `ChartPlan`, `ValidateResults`, `ModelJsonSchemaResults`
- PyCafe helpers such as `create_pycafe_url`

Consult `vizro-mcp/README.md`, `vizro-mcp/src/vizro_mcp/server.py`, and `vizro-mcp/tests/unit/vizro_mcp/test_server.py` when changing server behavior.

## Vizro-AI facts

- The package warns that `vizro-ai` is deprecated and points users to Vizro e2e-flow or Vizro-MCP.
- The current chart agent is `vizro_ai.agents._chart_agent.chart_agent`.
- `chart_agent` depends on a pandas `DataFrame` and response models such as `BaseChartPlan`.
- The `add_df` instruction helper samples the DataFrame and appends `DataFrame.info()` text; missing/non-DataFrame deps raise `ValueError`.

## Experimental chat facts

- Use `vizro_experimental.chat.models.chat.Chat` for the experimental chat model.
- `vizro_experimental.chat.popup` lazily exposes:
  - `add_chat_popup(generate_response=None, model=None, streaming=True, chat_id='chat_popup', ...)`
  - `create_dashboard_agent`
  - `make_generate_response`
- BYO `generate_response` mode should not force pydantic-ai/dashboard-agent imports; preserve that optional-dependency boundary.

## Dash components facts

Installed/generated components include:

```python
from vizro_dash_components import Cascader, Markdown

Cascader(id="regions", options=[{"label": "A", "value": "a"}], value=["a"])
Markdown(id="notes", children="**Markdown**", mathjax=True)
```

`Markdown` accepts `children`; do not use a `markdown_text` keyword in this snapshot.

Generated artifacts are created by:

```bash
cd vizro-dash-components
npm install --legacy-peer-deps
npm run build:js
# run with dash-generate-components available on PATH
 dash-generate-components ./src/ts/components vizro_dash_components -p package-info.json --ignore \.test\.
```
