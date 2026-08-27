# serving-remote troubleshooting

## Quick diagnosis map

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: vaex.server` or `No module named fastapi` | `vaex-server` or server dependencies are missing | Install the Vaex bundle or `vaex-server`; run `vaex server --help`; then run `python scripts/server_smoke.py --pretty`. |
| `TestClient` raises a Starlette/httpx error | FastAPI/Starlette requires the `httpx2` compatibility package in this stack | Install `httpx2` or align FastAPI/Starlette/httpx versions; avoid starting a listener just to diagnose this. |
| Importing `vaex.server.fastapi` downloads example data | The app initializes an example dataset by default | Use explicit local datasets, replace the dataset registry in TestClient smoke, or configure server files; do not rely on private cache paths. |
| `GET /dataset` returns unexpected names | Talking to the wrong process or relying on basename-derived names | Stop stale servers, start loopback with explicit `name=path`, and verify `/dataset` before requesting grids. |
| `GET /dataset/{id}` returns 404 | Dataset name mismatch or file failed to open | Check `GET /dataset`, CLI startup logs, and `name=path`; route file-open failures to `../io-conversion/SKILL.md`. |
| Histogram/heatmap returns 422 | JSON payload or query parameters do not match the input model | Compare against `references/rest-api.md`; include `dataset_id`, expression fields, numeric limits, and `shape_x`/`shape_y` as needed. |
| Histogram/heatmap returns 500 or TestClient exception | Bad expression, optional plotting dependency, or server bug | Print `response.text`; validate expression locally through `../expressions-analytics/SKILL.md`; for plot endpoints check `../visualization-jupyter/SKILL.md`. On newer Matplotlib builds, `matplotlib.cm.get_cmap` may be missing; apply the compatibility shim used in `scripts/server_smoke.py` or `scripts/plot_smoke.py` before retrying plot endpoints. |
| `OSError: address already in use` | Port collision or stale listener | Choose another port, bind to `127.0.0.1`, or terminate the exact stale process. |
| Remote `vaex.open` hangs or fails | Wrong scheme, host, port, path, proxy, or WebSocket route | Use `vaex+ws://` for local cleartext and `vaex+wss://` for TLS; verify `/dataset` over HTTP first. |
| `ValueError: No token provided` | Server requires token but client omitted or used wrong query/kwarg | Pass `token=...` or `token_trusted=...` as kwargs; avoid logging tokenized URLs. |
| Pickle/trusted operation fails | Normal token is not trusted | Avoid server-side arbitrary function serialization or use a trusted token only in a private trusted setup. |
| `--graphql` fails | Optional `vaex-graphql`, Graphene, or Starlette GraphQL mismatch | Treat GraphQL as optional; use REST/WebSocket unless the user specifically needs GraphQL. |

## Missing `vaex-server` or server CLI

Check the active environment rather than the source checkout:

```bash
python - <<'PY'
import vaex
import vaex.server.fastapi
print(vaex.__version__)
PY
vaex server --help
```

Fixes:

1. Install the public Vaex package set for the environment, commonly `pip install vaex` or `conda install -c conda-forge vaex`.
2. If installing packages separately, ensure `vaex-server` is present along with FastAPI/Uvicorn/Tornado dependencies.
3. Use the bundled `scripts/server_smoke.py` to verify the installed package APIs without a listener.
4. Do not import modules from a repository checkout path to work around an incomplete installation.

## FastAPI `TestClient` and `httpx2`

In the verified Vaex 4.19.0 environment, FastAPI `TestClient` required the `httpx2` compatibility package. Symptoms may include an exception mentioning Starlette's explicit `httpx2` requirement or an incompatible `Client.__init__` signature.

Resolution pattern:

```bash
python -m pip install httpx2
python scripts/server_smoke.py --pretty
```

If that is not acceptable in the user's environment, fall back to:

- `vaex server --help` for CLI presence.
- A local loopback listener only when authorized.
- Direct FastAPI import diagnostics without constructing `TestClient`.

Do not start a public listener as a workaround for TestClient dependency errors.

## Example dataset download/cache surprise

The FastAPI module initializes server state at import time and may ensure an `example` dataset. In some installations this downloads Vaex's example data into the user's Vaex data/cache location.

Avoid surprises:

- Prefer tiny explicit in-memory DataFrames in TestClient checks.
- Prefer explicit `name=path` files when starting `vaex server`.
- If example-data download fails because the environment is offline, do not treat that as proof that serving is broken. Re-run with explicit local datasets or monkeypatch/replace the registry in a smoke script.
- Do not mention or depend on private cache paths in runtime instructions.

## Host, port, and listener cleanup

Safe defaults:

```bash
vaex server --host 127.0.0.1 --port 8081 dataset=/path/to/data.hdf5
```

Troubleshooting:

- `0.0.0.0` binds all interfaces. Use it only when the user intentionally exposes the service and has handled firewall/authentication/proxy concerns.
- Port collisions produce address-in-use errors; choose another port or terminate the exact old process.
- Container and reverse-proxy deployments may need `--base-url` for correct printed URLs; it does not change where the process binds.
- Always record how to stop the listener. Automated checks should use TestClient or start/stop a subprocess with a timeout.

## Dataset name parsing problems

The CLI accepts plain paths and `name=path` entries. Failures often come from ambiguous names:

- `foo=/data/a.hdf5` publishes `foo`.
- `/data/a.hdf5` publishes `a`.
- Two files with the same basename collide or overwrite in the server dataset map.
- Dataset names become URL path segments. Avoid spaces, slashes, `?`, `#`, and `=`.
- If a path itself contains `=`, the CLI split can misinterpret it. Rename the file, symlink it, or use a path without `=`.

Always query `GET /dataset` first.

## REST payload and expression failures

For `422`:

- Ensure POST bodies are sent as JSON, not form data.
- `shape` is for histograms; `shape_x` and `shape_y` are for heatmaps.
- Required names are `expression` for histogram, `expression_x`/`expression_y` for heatmap.
- Use `null` for missing `filter` or limits, not the string `'None'`.

For expression failures:

- First confirm the column exists via `/dataset/{dataset_id}` schema.
- Test the expression locally on a small DataFrame or through `../expressions-analytics/SKILL.md`.
- Use virtual columns as a JSON object: `{'derived': 'x/y'}`.
- Remember that `filter` is an expression string evaluated by Vaex; syntax and quoting matter.

## Remote URL scheme and path failures

Use explicit remote schemes:

```python
df = vaex.open('vaex+ws://127.0.0.1:8081/sales')   # local cleartext
df = vaex.open('vaex+wss://data.example.org/sales') # TLS/proxy
```

Common mistakes:

- Using `https://.../dataset/sales` with `vaex.open`; that is a REST metadata URL, not a WebSocket remote DataFrame URL.
- Including `/dataset/` in the remote DataFrame URL. The WebSocket remote name is the final dataset segment, e.g. `/sales`.
- Forgetting the server's base path when it is mounted behind a proxy.
- Trying `http://` expecting a remote DataFrame. HTTP remote DataFrame support is not implemented in this version; use REST requests manually.
- Neglecting `client.close()` when using `vaex.server.connect` directly.

## Token and trusted-token failures

Token behavior is easiest to debug with a tiny local server and one scalar aggregation. Do not log real tokens.

Patterns:

```python
# Good: secret stays out of the URL string.
df = vaex.open('vaex+ws://127.0.0.1:9000/df', token=token)

# Trusted token only for private clients that may deserialize trusted functions.
df = vaex.open('vaex+ws://127.0.0.1:9000/df', token_trusted=trusted_token)
```

Interpretation:

- `No token provided, not authorized`: missing or wrong token.
- Error mentioning pickle/trusted deserialization: operation requires trusted token; avoid arbitrary `apply(lambda...)` patterns unless the security boundary allows it.
- Tokenized query strings are supported but unsafe to paste. Prefer kwargs or environment variables.

## GraphQL optional dependency mismatch

GraphQL symptoms include:

- `ModuleNotFoundError: No module named 'vaex.graphql'`.
- `ModuleNotFoundError` or import errors for `graphene`, `graphene_tornado`, or `starlette.graphql`.
- Schema errors caused by Graphene v2/v3 differences.
- `/graphql` missing even when REST endpoints work.

Actions:

1. Confirm whether the user actually needs GraphQL. If not, continue with REST/WebSocket.
2. Run an import/schema smoke rather than starting a public listener:

   ```bash
   python - <<'PY'
   import vaex, vaex.graphql
   df = vaex.from_arrays(x=[1, 2], y=[3, 4])
   result = df.graphql.execute('{ df { count mean { y } } }')
   print(result.errors, result.data)
   PY
   ```

3. If enabling `vaex server --graphql`, pin a compatible GraphQL stack in the user's environment and test locally.
4. Treat GraphQL as optional for the serving skill unless it is explicitly the task target.

## Long-running listener boundaries

Automated verification should not leave listeners running. Preferred order:

1. `python scripts/server_smoke.py --pretty` using TestClient.
2. CLI help: `vaex server --help`.
3. If process-boundary behavior is required, start `vaex server` in a subprocess bound to `127.0.0.1`, wait for `/dataset`, run bounded requests, then terminate the subprocess in `finally`/trap cleanup.

Never run unbounded public listeners, never embed credentials in commands, and never treat an external public service as required proof.

## Source-script mapping

- Modern serving behavior is distilled from the installed public `vaex server` console entry and the FastAPI server package surface. The bundled `scripts/server_smoke.py` wraps behavior with public imports and TestClient rather than copying source files.
- The legacy `bin/webveax` script is reference-only and intentionally excluded. It is a legacy browser/server workflow with broader side effects and overlapping responsibility; do not copy or run it for runtime guidance.
