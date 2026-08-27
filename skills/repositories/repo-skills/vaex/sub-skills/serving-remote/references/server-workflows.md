# Vaex server workflows

## Mental model

`vaex-server` exposes Vaex DataFrames in two complementary ways:

- **FastAPI REST app**: list datasets, inspect schemas, request histogram/heatmap data, and request quick PNG plot endpoints over HTTP. This is the surface used by non-Python clients and by safe in-process `TestClient` smoke checks.
- **WebSocket remote DataFrame**: Python clients call `vaex.open('vaex+ws://host:port/dataset')`, `vaex.open('vaex+wss://host/dataset')`, or `vaex.server.connect(...)`. The data stays on the server; Vaex sends method calls/tasks and compact results such as scalar aggregations or grids.

Use REST when the client is JavaScript, curl, a web dashboard, or another language. Use the remote DataFrame API when the client is Python and should retain Vaex DataFrame semantics.

## Confirm installation and help

```bash
python -c "import vaex, vaex.server.fastapi; print(vaex.__version__)"
vaex server --help
```

The server subcommand accepts:

```text
vaex server [--add-example] [--host HOST] [--base-url BASE_URL] [--port PORT]
            [--verbose | -v] [--quiet | -q] [--graphql]
            [filename ...]
```

Notes:

- `filename ...` may be ordinary Vaex-openable files.
- `name=path` publishes a dataset under a stable explicit name.
- Plain `path` uses the file basename without its extension as the dataset name.
- `--add-example` adds the Vaex example dataset in addition to explicitly listed files.
- If no datasets are configured, the server falls back to the example dataset. That may trigger example-data download/cache setup in some installations; prefer explicit tiny local files for deterministic checks.
- `--graphql` is optional and needs a compatible GraphQL dependency stack.

Route broad command maps, settings command output, and non-server options to `../cli-settings/SKILL.md`.

## Safe local smoke: no listener

Before starting a listener, use the bundled smoke helper:

```bash
python scripts/server_smoke.py --help
python scripts/server_smoke.py --pretty
```

By default the helper imports the installed Vaex server package surface, patches the example-data hook to a tiny in-memory DataFrame, and runs safe FastAPI/TestClient route checks without binding a socket. Use `--skip-route-checks` when you only want import/help diagnostics. Use `--server-help` to confirm the server parser, and use `--histogram`, `--heatmap`, `--dataset-metadata`, `--include-plot-endpoints`, or `--include-openapi` only when touching the local Vaex example-data/cache layer is acceptable.

If you opt into a custom TestClient check, use this pattern:

```python
import numpy as np
import vaex
import vaex.server.fastapi as vf
from fastapi.testclient import TestClient

one = vaex.from_arrays(x=np.arange(8.0), y=np.arange(8.0) * 2)
one.name = 'one'
two = vaex.from_arrays(x=np.arange(5.0), y=np.arange(5.0) + 10)
two.name = 'two'

vf.datasets.clear()
vf.datasets.update({'one': one.dataset, 'two': two.dataset})
vf.update_service({'one': one, 'two': two})

client = TestClient(vf.app, raise_server_exceptions=True)
assert client.get('/dataset').json() == ['one', 'two']
assert client.get('/dataset/one').status_code == 200
assert client.post('/histogram', json={
    'dataset_id': 'one',
    'expression': 'x',
    'min': 0,
    'max': 7,
    'shape': 4,
}).status_code == 200
```

Caveat: importing `vaex.server.fastapi` can initialize the example dataset before you replace the registry, depending on Vaex settings. If this matters, keep to the bundled helper's default mode or run app/route checks in a controlled environment and avoid relying on example cache state.

## Manual loopback listener

Only start a listener when the task needs another process, WebSocket behavior, curl, or browser access. Bind to loopback unless the user explicitly asks to expose it.

```bash
# First prepare a local Vaex-openable file through the IO sub-skill if needed.
vaex server --host 127.0.0.1 --port 8081 --base-url 127.0.0.1:8081 \
  one=/path/to/one.hdf5 two=/path/to/two.hdf5
```

Expected log lines identify each dataset:

```text
one:  http://127.0.0.1:8081/dataset/one for REST or ws://127.0.0.1:8081/one for websocket
two:  http://127.0.0.1:8081/dataset/two for REST or ws://127.0.0.1:8081/two for websocket
```

Then query locally:

```bash
curl -s http://127.0.0.1:8081/dataset
curl -s http://127.0.0.1:8081/dataset/one
curl -s 'http://127.0.0.1:8081/histogram/one/x?min=0&max=10&shape=8'
```

Cleanup boundary:

- Keep the terminal/process handle visible.
- Stop with `Ctrl-C` or terminate the exact process you started.
- Do not leave a background `0.0.0.0` service running from an automated check.

## Dataset naming rules

Use explicit names for stable URLs:

```bash
vaex server --host 127.0.0.1 --port 8081 sales=/data/sales.hdf5 events=/data/events.arrow
```

Rules and pitfalls:

- The CLI splits `name=path` at `=`. Avoid dataset names containing `=`.
- Stable names should be URL-safe identifiers such as `sales_2024` or `events`; avoid spaces and slashes.
- Dataset names become path segments in `/dataset/{dataset_id}`, `/histogram/{dataset_id}/{expression}`, `/heatmap/{dataset_id}/{x}/{y}`, and WebSocket remote URLs.
- If you pass a plain filename, the name is derived from the basename with the extension removed. This can collide when two files share a basename.
- File opening errors are IO problems; route format conversion and plugin diagnosis to `../io-conversion/SKILL.md`.

## Base URL and reverse proxy notes

`--base-url` controls the URL printed in startup logs. If omitted, the server uses `<host>:<port>` except port 80, where it prints just `<host>`.

Use `--base-url` when a reverse proxy, container port mapping, or TLS endpoint differs from the bind address:

```bash
vaex server --host 0.0.0.0 --port 8081 --base-url data.example.org datasets=/data/datasets.hdf5
```

Guidance:

- Bind address (`--host`) is where the process listens.
- External base URL is what clients should use.
- For local checks, prefer `--host 127.0.0.1 --base-url 127.0.0.1:PORT`.
- For TLS, Python remote clients normally use `vaex+wss://...`; without TLS, use `vaex+ws://...` or `ws://...`.

## Two-dataset heatmap from another process

This is the key difficult serving case: expose stable names, then query a compact grid from a separate process.

1. Convert or create two local Vaex-openable files. Route the conversion step to `../io-conversion/SKILL.md` if the inputs are CSV/Parquet/Pandas.
2. Start loopback with explicit names:

   ```bash
   vaex server --host 127.0.0.1 --port 8081 left=./left.hdf5 right=./right.hdf5
   ```

3. In another process, query the dataset registry and heatmap:

   ```python
   import requests

   base = 'http://127.0.0.1:8081'
   assert set(requests.get(f'{base}/dataset', timeout=5).json()) >= {'left', 'right'}
   payload = {
       'dataset_id': 'right',
       'expression_x': 'x',
       'expression_y': 'y',
       'min_x': 0,
       'max_x': 10,
       'min_y': 0,
       'max_y': 10,
       'shape_x': 16,
       'shape_y': 16,
       'filter': None,
       'virtual_columns': {},
   }
   response = requests.post(f'{base}/heatmap', json=payload, timeout=10)
   assert response.status_code == 200, response.text
   data = response.json()
   assert data['dataset_id'] == 'right'
   assert len(data['centers_x']) == 16
   assert len(data['centers_y']) == 16
   assert len(data['values']) == 16
   ```

4. Stop the listener. Do not reuse a stale background server without first checking its dataset list.
