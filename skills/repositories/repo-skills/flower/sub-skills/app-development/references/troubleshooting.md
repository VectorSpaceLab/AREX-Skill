# Troubleshooting

Start with `scripts/check_flower_app.py`. It validates `pyproject.toml`, checks that the
component strings resolve, and runs a tiny in-memory Flower app smoke.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `A \`ClientApp\` cannot make use of a \`client_fn\` that does not have a signature in the form: \`def client_fn(context: Context)\`` | Wrong or outdated `client_fn` signature | Change the function to accept a single `Context` argument. If the legacy form uses `cid` or a `str` annotation, Flower will warn and adapt it. |
| `Cannot register train/evaluate/query function ... use either \`@app.fn()\` or \`client_fn\`, but not both` | Mixed `client_fn` and decorator-based routing | Choose one path: legacy `client_fn` or new-style `@app.train()` / `@app.evaluate()` / `@app.query()`. |
| `Invalid message type: ...` or `Cannot register ... function with name '...'` | Bad message category/action or invalid action name | Use `train`, `evaluate`, or `query`, and make sure the action suffix is a valid Python identifier. |
| `Invalid arguments for Message...` | Constructed a `Message` with the wrong positional/keyword combination | Use one of the documented forms: instruction message with content, or reply message with `reply_to`. Never set both content and error. |
| `TypeError` from `RecordDict`, `ArrayRecord`, `ConfigRecord`, or `MetricRecord` | Wrong payload types | Use `ArrayRecord` for arrays, `MetricRecord` for scalar metrics, and `ConfigRecord` for runtime values. Keep list values homogeneous. |
| `KeyError` on `context.run_config[...]` or `context.node_config[...]` | Missing config key | Add the key to `[tool.flwr.app.config]`, override it with `--run-config`, or populate the node config in the launcher. |
| `Unable to load module ...` / `Unable to find attribute ...` | Malformed `tool.flwr.app.components` entry | Fix the `<module>:<attribute>` string and ensure the project directory is importable. |
| `Property \"publisher\" missing in [tool.flwr.app]` or `Missing [tool.flwr.app.components] section` | Incomplete `pyproject.toml` | Add the required Flower app metadata and component paths. |
| Deprecated alias warnings from `RecordDict` or `Message` helpers | Old compatibility paths | Replace `parameters_records` / `metrics_records` / `configs_records` with the typed views, and replace `create_reply` / `create_error_reply` with direct `Message(..., reply_to=...)` calls. |
| `NumPyClient` returned from `client_fn` is converted with a warning | Legacy client factory returns `NumPyClient` | Convert explicitly with `NumPyClient.to_client()` so the compatibility warning goes away. |
| `ValueError` when combining `@app.main()` with deprecated direct `ServerApp` constructor args | Mixed old and new server styles | Prefer `ServerApp()` + `@app.main()` for new code. Keep `server_fn` only for legacy compatibility. |

## Quick isolation order
1. Validate the app wiring with `scripts/check_flower_app.py`.
2. Fix any `pyproject.toml` or import-path errors.
3. Check message payload types and `Context` key access.
4. Rerun the smoke, then rerun `flwr run`.

## Good defaults
- Use kebab-case config keys in `pyproject.toml`.
- Read run values through `context.run_config`.
- Read per-node values through `context.node_config`.
- Keep app objects stateless and store persistent client data in `context.state`.
