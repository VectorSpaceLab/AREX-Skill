---
name: dash-components-build
description: "Use and maintain Vizro Dash Components, including
  Cascader/Markdown props, TypeScript source, generated Python wrappers, npm
  build, and browser-test constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Dash Components Build

Use this sub-skill when a task involves `vizro-dash-components`, `vizro_dash_components`, Cascader, Markdown, TypeScript/React component source, generated Python wrappers, webpack, or Dash component browser tests.

Route elsewhere when the task is mainly about using these components inside a broader Vizro dashboard: also load `../core-components-data-actions/SKILL.md`.

## Component usage

```python
from vizro_dash_components import Cascader, Markdown

cascader = Cascader(
    id="region-picker",
    options=[{"label": "Europe", "value": "europe", "children": [{"label": "France", "value": "fr"}]}],
    value=["europe", "fr"],
)

markdown = Markdown(
    id="notes",
    children="## Notes\n\nUse **Markdown** and optional MathJax.",
    mathjax=True,
)
```

In this snapshot, `Markdown` accepts `children`; `markdown_text` is not a valid keyword.

## Source-of-truth rule

- Edit TypeScript/React source under `vizro-dash-components/src/ts/`.
- Do not hand-edit generated files in `vizro-dash-components/vizro_dash_components/`.
- Regenerate Python wrappers and JS bundles after source changes.

## Build pipeline

From `vizro-dash-components/`:

```bash
npm install --legacy-peer-deps
npm run build
```

If `dash-generate-components` is not found during the backend generation step, run the two phases explicitly with a Python environment where `dash[dev]` is installed:

```bash
npm run build:js
dash-generate-components ./src/ts/components vizro_dash_components -p package-info.json --ignore \.test\.
```

Why `--legacy-peer-deps`: npm 11 strict peer resolution can reject the package's current React 18 / `react-markdown@4.3.1` combination; legacy peer resolution completed the verified build.

## Testing

Browser-backed package tests:

```bash
cd vizro-dash-components
hatch run test
```

These require Chrome/Chromium plus Dash/Selenium fixtures. If no browser is installed, run build/import/static checks and mark browser tests blocked rather than changing code blindly.

Quick import smoke after install/build:

```bash
python - <<'PY'
from vizro_dash_components import Cascader, Markdown
print(Cascader(id='c', options=[{'label': 'A', 'value': 'a'}], value=['a']))
print(Markdown(id='m', children='**ok**'))
PY
```

## Development patterns

- Each `.tsx` file under `src/ts/components/` becomes a Python Dash component.
- Props should have useful TypeScript types and JSDoc comments because they feed Python docstrings/metadata.
- Use `setProps({...})` for Dash callback-updated properties.
- Internal React helpers belong in `src/ts/fragments` or `src/ts/utils`, not exported Dash components.
- Keep generated package metadata (`package-info.json`, `metadata.json`, `_imports_.py`) in sync through generation.

## Common failures

- `ModuleNotFoundError` for `_imports_` or missing component classes: generated wrappers were not produced or the local wheel was built before generation.
- `dash-generate-components: not found`: install `dash[dev]` in the environment or run through Hatch's generation command.
- Browser test failures: confirm Chrome/Chromium first; then inspect component props/callback behavior.
- Python prop error for Markdown: use `children`, not `markdown_text`.

## Evidence anchors

- `vizro-dash-components/README.md`
- `vizro-dash-components/AGENTS.md` / `CLAUDE.md`
- `vizro-dash-components/package.json`
- `vizro-dash-components/src/ts/components/*`
- `vizro-dash-components/examples/app.py` and `examples/pages/*`
- `vizro-dash-components/tests/test_cascader.py`
