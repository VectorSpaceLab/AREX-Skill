# Renderer Internals

## When to read

Read this for dash-renderer hydration, callback queues, layout traversal,
clientside function execution, `setProps`, and the browser-side WebSocket client.

## Initialization flow

The renderer boot sequence is:

1. Create the DashRenderer entry point.
2. Create the React root and app provider.
3. Fetch `/_dash-layout` and `/_dash-dependencies`.
4. Build the component ID path map and callback dependency graph.
5. Hydrate initial outputs.
6. Render the component tree and register observers for callback processing.

## Layout crawling

The renderer traverses `children` plus generated `_children_props` patterns.
Generated component wrappers provide `_children_props` so nested component props
inside arrays or objects are visible to callback dependency/path discovery.

Pattern examples:

| Pattern | Meaning |
| --- | --- |
| `children` | ordinary child prop |
| `options.[]` | every item in an array prop may be a component |
| `options.[].label` | nested field inside every array item may be a component |
| `items.{}` | values in an object prop may be components |

## Callback queue states

Renderer callback processing moves callback records through states such as:

- requested
- prioritized
- executing
- watched
- executed
- stored
- blocked

Use this model when diagnosing callback scheduling, deduplication, loading state,
or race-condition bugs.

## `setProps` path

When a component calls `setProps`:

1. DashWrapper updates the component props in the Redux layout.
2. Watched callback inputs are found from the dependency graph.
3. Matching callbacks are requested and eventually executed.
4. Results are applied back to layout props and may trigger downstream callbacks.

If `setProps` is called but no callback fires, inspect the ID/path map and the
callback graph rather than only the component implementation.

## Browser APIs

Dash exposes browser APIs:

- `window.dash_clientside`: clientside callback functions, `no_update`,
  `PreventUpdate`, callback context, URL cleaning, and `set_props`.
- `window.dash_component_api`: component integration helpers such as layout
  lookup, context/hooks, and external rendering wrappers.

## WebSocket client overview

The renderer uses a SharedWorker-based WebSocket client when WebSocket callbacks
are enabled and the browser supports SharedWorker. The server-side WebSocket
rules live in the server backend sub-skill; this reference is for frontend
routing and callback-response behavior.

## Renderer command

`renderer` is the build-process command for renderer assets. Safe first check:

```bash
python path/to/component-renderer-development/scripts/check_renderer_cli.py --json
```

Full renderer builds require Node dependencies and can be much heavier than a
parser/help check.
