---
name: component-renderer-development
description: "Use for Dash component wrapper generation, built-in component
  packages, resources, and dash-renderer internals."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Dash Component and Renderer Development

Use this sub-skill when a task concerns component wrapper generation, built-in
Dash component packages, resource loading, or the dash-renderer frontend and its
callback pipeline.

## Start here

1. Read [references/component-generation.md](references/component-generation.md)
   for component metadata, generated wrappers, and `dash-generate-components`.
2. Read [references/resources-and-react.md](references/resources-and-react.md)
   for `_js_dist`, `_css_dist`, resource loading, and React version notes.
3. Read [references/renderer-internals.md](references/renderer-internals.md)
   for renderer hydration, callback queues, `setProps`, and clientside runtime.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when a
   build, wrapper, bundle, or React runtime issue fails.
5. Run [scripts/check_component_generator_cli.py](scripts/check_component_generator_cli.py),
   [scripts/check_update_components_cli.py](scripts/check_update_components_cli.py),
   and [scripts/check_renderer_cli.py](scripts/check_renderer_cli.py) for safe CLI
   help checks before heavier builds.

## Main routes

### Generate or refresh component wrappers

Use this route when a task mentions component metadata, wrapper generation, or
maintaining built-in component packages such as `dcc`, `html`, or `dash_table`.

### Inspect renderer behavior

Use this route for callback hydration, layout crawling, state paths, shared
worker/WebSocket client behavior, `window.dash_component_api`, or React/runtime
compatibility problems.

### Work on resource loading and React versions

Use this route when a task mentions resource URLs, asset fingerprints,
`serve_locally`, `_js_dist`, `_css_dist`, or React version/shim behavior.

## Route elsewhere

- App-level callback and page use: [app callback workflows](../app-callback-workflows/SKILL.md).
- Server-side async, WebSocket, background, or MCP runtime behavior:
  [server backends and async](../server-backends-and-async/SKILL.md).
- Choosing focused tests or build/lint commands:
  [testing and maintenance](../testing-and-maintenance/SKILL.md).

## Validation checklist

Before marking component or renderer work complete:

- The component package can be imported from Dash and its generated wrapper class
  names are available.
- `dash-generate-components`, `dash-update-components`, and `renderer` help text
  are healthy before a full build is attempted.
- `_js_dist`/`_css_dist` entries use the correct resource fields and do not point
  at the wrong namespace or package path.
- Renderer changes are checked against the current React/runtime assumptions.
- If a build script needs Black or other formatter/tooling, the failure mode is
  documented and the prerequisite is installed first.
