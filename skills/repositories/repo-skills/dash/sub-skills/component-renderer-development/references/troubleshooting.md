# Component and Renderer Troubleshooting

## When to read

Read this when component imports, wrapper generation, resource loading, renderer
callbacks, React runtime, or Node-based builds fail.

## Generated wrapper failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `dash.html` has no `Div` or `dash.dcc` has no `Graph` in a checkout | Generated built-in wrappers are missing or stale | Run the component update/generation workflow in the checkout or install a released Dash package. |
| `dash-generate-components` fails with no metadata output | React source path, ignore pattern, Node modules, or metadata extraction failed | Run `dash-generate-components --help`, verify the source path and package metadata, then install Node dependencies for the component package. |
| Generated Python wrappers have invalid formatting | Formatter missing or incompatible | Install the expected formatter and rerun generation; do not hand-edit generated wrappers unless the generator is also fixed. |

## Node/npm and build failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `npm ci` fails | Lockfile/toolchain mismatch or network resolution | Verify Node version from the checkout's version file and keep full npm output. |
| Component build fails at webpack | JS/TS source or dependency issue | Run the package-specific build with full output; do not run all packages if only one changed. |
| Build script reports missing `black` | Python formatter expected by component backend generation | Install Black in the build environment before rerunning the component build. |
| Full renderer build is slow or flaky | Node dependencies/browser launcher/build output are heavy | Use CLI help and focused renderer tests first; run full build only when renderer assets changed. |

## Resource and browser failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Browser cannot resolve component type | Wrong `namespace`, missing JS bundle, or resource did not load | Check component `namespace`, `_js_dist`, and browser network/console output. |
| `serve_locally=True` warns about unavailable local resource | Resource only has external URL or package file missing | Provide a packaged resource path or use `external_scripts`/`external_stylesheets` for external-only assets. |
| `app.index()` raises `FileNotFoundError` for `dash/deps/polyfill...` or another Dash JS dependency | Editable checkout imports Python but lacks packaged frontend resource files | For app-use tasks, install a released wheel or package with included JS resources. For maintainer tasks, rebuild or restore frontend bundles, then rerun focused config/resource tests instead of treating the failure as a callback bug. |
| Dev bundle not loaded | Dev tools/dev bundles not enabled | Use the appropriate dev tools settings when debugging renderer code. |
| `ReactJSXRuntime is not defined` | Bundle externalized JSX runtime incorrectly or React 19 shim/load order is wrong | Use the defensive external expression and make sure Dash's React shim loads before component bundles. |
| Nested components not discovered | `_children_props` metadata missing or incorrect | Regenerate component wrappers and confirm the nested prop pattern is present. |

## Renderer callback failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `setProps` updates layout but callback not requested | Component ID not in path map or property not watched | Inspect ID path mapping and callback dependency definitions. |
| Loading spinner never clears | Callback queue stuck or server response missing | Inspect requested/executing callbacks and server errors. |
| WebSocket callback path not used | WebSocket disabled or unavailable in browser | Confirm config and SharedWorker support; route server-side checks to backend sub-skill. |

## Safe diagnostics

Use the bundled scripts before heavier commands:

```bash
python path/to/component-renderer-development/scripts/check_component_generator_cli.py --json
python path/to/component-renderer-development/scripts/check_update_components_cli.py --json
python path/to/component-renderer-development/scripts/check_renderer_cli.py --json
```
