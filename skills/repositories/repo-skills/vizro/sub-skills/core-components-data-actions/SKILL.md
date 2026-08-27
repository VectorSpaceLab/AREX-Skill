---
name: core-components-data-actions
description: "Compose Vizro pages with components, data, filters, selectors,
  tables, custom components, and action callbacks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Core Components, Data, and Actions

Use this sub-skill when a task asks for Vizro model composition below the dashboard/page level: cards, graphs, tables, filters, selectors, parameters, buttons, actions, data registration, custom Dash components, or graph/table interactions.

Route elsewhere when the task is mainly about:
- Dashboard skeleton, YAML loading, or app run/deploy: `../core-dashboard-build/SKILL.md`.
- Chart/figure implementation details: `../charts-and-figures/SKILL.md`.
- `vizro-dash-components` TypeScript/generated wrappers: `../dash-components-build/SKILL.md`.

## Component authoring pattern

Typical page composition uses `vizro.models` aliases:

```python
import vizro.models as vm
import vizro.plotly.express as px

page = vm.Page(
    title="Sales",
    components=[
        vm.Card(text="Summary"),
        vm.Graph(figure=px.scatter(px.data.iris(), x="sepal_width", y="sepal_length", color="species")),
        vm.Table(figure=px.data.tips().head(20)),
    ],
    controls=[
        vm.Filter(column="species"),
    ],
)
```

Always check the live field list when uncertain:

```bash
python scripts/inspect_vizro_schema.py --models Card Graph Table AgGrid Filter Parameter Button Slider Checklist Dropdown
```

## Data patterns

- For small examples and chart code, pass DataFrames directly into `vizro.plotly.express` functions.
- For reusable dashboard datasets, use `vizro.managers.data_manager` with stable string keys, as shown in the YAML example.
- Register data before model build if a YAML dashboard references data by key.
- Avoid hidden global state in tests: reset/rebuild data-manager state or use isolated small fixtures when possible.

Example registration:

```python
from vizro.managers import data_manager
import vizro.plotly.express as px

data_manager["iris"] = px.data.iris()
```

## Controls and selectors

- Use Vizro `Filter`/selector models instead of manual Dash callbacks for normal dashboard filtering.
- Match filter columns to DataFrame column names used in associated figures/tables.
- For model errors, check whether the control belongs in `controls`, whether a target component is expected, and whether the column name exists.

## Actions and callbacks

- Built-in actions live under `vizro.actions`; custom actions are documented in the custom-actions tutorial.
- Wire graph/table actions through Vizro's action model patterns before dropping down to raw Dash callbacks.
- For graph/table interactions, inspect `graph-table-actions.md` and the e2e-flow `wiring-vizro-actions` reference.
- Keep action inputs/outputs stable and named; most action bugs are mismatched component ids, wrong event property, or returning a value with the wrong shape.

## Custom components

- Prefer Vizro model components. Use raw Dash or custom components only when a component cannot be represented by an existing model.
- For `vizro-dash-components` (`Cascader`, `Markdown`), route to `../dash-components-build/SKILL.md` for props and generation.
- If adding a new custom model/component to `vizro-core`, update docs/examples and focused model tests.

## Debug checklist

1. Can a minimal `Dashboard` with one `Page` and one `Card` build?
2. Does each component instantiate independently?
3. Do data keys/columns exist before build?
4. Are filters/selectors attached at the page/control level expected by current schemas?
5. Does an action fail during Pydantic validation, during Dash callback registration, or during browser interaction?
6. If browser-only behavior is involved, confirm Chrome/Chromium availability before treating e2e failures as app regressions.

## Evidence anchors

- `vizro-core/src/vizro/models/__init__.py`: exported component/control/action model classes.
- `vizro-core/src/vizro/actions/__init__.py`: built-in action surface.
- `vizro-core/src/vizro/managers/_data_manager.py`: data registration and lookup behavior.
- Docs: `data.md`, `actions.md`, `filters.md`, `selectors.md`, `table.md`, `graph-table-actions.md`, `custom-components.md`.
- Examples: `vizro-core/examples/tutorial-custom-actions/app.py`, YAML data registration example.
