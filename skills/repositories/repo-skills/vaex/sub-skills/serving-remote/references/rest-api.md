# Vaex server REST API

The FastAPI REST surface is for non-Python clients or simple process-boundary checks. It returns JSON for metadata and grid endpoints, and PNG bytes for quick plot endpoints. For the meaning of histogram/heatmap grids, selections, `what`, or plotting choices, route to `../expressions-analytics/SKILL.md` and `../visualization-jupyter/SKILL.md`.

## Status and header signals

Expected success signals:

- `200 OK` for dataset list, dataset metadata, histogram, heatmap, and plot endpoints.
- JSON endpoints return `application/json` bodies.
- Plot endpoints return PNG image bytes.
- Responses include Vaex timing headers when they pass through the FastAPI middleware:
  - `X-Process-Time`: elapsed server-side request time in seconds as a string.
  - `X-Data-Passes`: number of Vaex executor data passes during the request as a string.

Expected failure signals:

- `404` when `dataset_id` is not in the server registry.
- `413` when Vaex task checking rejects a request, surfaced as plain text.
- `422` from FastAPI/Pydantic when required fields are missing or have invalid types.
- `500` or propagated exceptions in `TestClient(raise_server_exceptions=True)` for server bugs or dependency mismatches.

Always print or preserve `response.text` for unexpected non-200 responses; FastAPI error bodies often identify the missing field or failing expression.

## Dataset endpoints

### `GET /dataset`

Lists dataset names.

```bash
curl -s http://127.0.0.1:8081/dataset
```

Response shape:

```json
["example", "sales"]
```

Use this before any detailed request to confirm that you are talking to the expected server process.

### `GET /dataset/{dataset_id}`

Returns metadata about a dataset.

```bash
curl -s http://127.0.0.1:8081/dataset/sales
```

Response shape:

```json
{
  "id": "sales",
  "row_count": 1000000,
  "schema": {
    "x": "float64",
    "y": "float64",
    "category": "string"
  }
}
```

Validation checklist:

- `id` equals the path segment requested.
- `row_count` is present and non-negative.
- `schema` maps column names to dtype strings.
- If this returns `404`, re-check dataset names, CLI naming, or the file-open step.

## Histogram endpoints

Vaex exposes both GET and POST histogram forms.

### `GET /histogram/{dataset_id}/{expression}`

Query parameters are parsed into the histogram input model.

```bash
curl -s 'http://127.0.0.1:8081/histogram/sales/x?min=0&max=100&shape=32'
```

Key query parameters:

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `dataset_id` | path/string | required | Dataset name. |
| `expression` | path/string | required | Vaex expression or column for the x axis. |
| `shape` | integer | `128` | Number of bins. |
| `min` | number or string | auto | Lower limit. If omitted, server computes limits. |
| `max` | number or string | auto | Upper limit. If omitted, server computes limits. |
| `filter` | string/null | `null` | Vaex selection/filter expression used for the count. |
| `virtual_columns` | object | not practical in GET | Mapping of virtual column names to expression strings; prefer POST for this. |

Response shape:

```json
{
  "dataset_id": "sales",
  "centers": [1.5625, 4.6875],
  "values": [12, 30]
}
```

`centers` length and `values` length should equal `shape`.

### `POST /histogram`

POST is better for JavaScript/Python clients because it can send `filter` and `virtual_columns` cleanly.

```python
import requests

payload = {
    'dataset_id': 'sales',
    'expression': 'log_sales',
    'shape': 64,
    'min': 0,
    'max': 10,
    'filter': 'region == "EU"',
    'virtual_columns': {
        'log_sales': 'log1p(sales)'
    },
}
response = requests.post('http://127.0.0.1:8081/histogram', json=payload, timeout=10)
assert response.status_code == 200, response.text
hist = response.json()
```

POST input model:

```json
{
  "dataset_id": "sales",
  "expression": "x",
  "shape": 128,
  "min": null,
  "max": null,
  "filter": null,
  "virtual_columns": {}
}
```

Implementation note: the histogram response model contains `dataset_id`, `centers`, and `values`. Some installed versions may include an `expression` field in the POST response body even if the declared output model is narrower; consumers should rely on the documented stable fields.

## Heatmap endpoints

Vaex exposes both GET and POST heatmap forms.

### `GET /heatmap/{dataset_id}/{expression_x}/{expression_y}`

```bash
curl -s 'http://127.0.0.1:8081/heatmap/sales/x/y?min_x=0&max_x=10&min_y=0&max_y=20&shape_x=16&shape_y=8'
```

Key query parameters:

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `dataset_id` | path/string | required | Dataset name. |
| `expression_x` | path/string | required | X-axis expression. |
| `expression_y` | path/string | required | Y-axis expression. |
| `shape_x` | integer | `128` | X bins. |
| `shape_y` | integer | `128` | Y bins. |
| `min_x`, `max_x` | number/string/null | auto | X limits. |
| `min_y`, `max_y` | number/string/null | auto | Y limits. |
| `filter` | string/null | `null` | Vaex selection/filter expression. |
| `virtual_columns` | object | not practical in GET | Prefer POST when needed. |

Response shape:

```json
{
  "dataset_id": "sales",
  "expression_x": "x",
  "expression_y": "y",
  "centers_x": [0.5, 1.5],
  "centers_y": [5.0, 15.0],
  "values": [[3, 1], [0, 4]]
}
```

Validation checklist:

- `len(centers_x) == shape_x`.
- `len(centers_y) == shape_y`.
- `values` is a nested list representing the grid returned by Vaex. Treat orientation/transposition as a visualization concern and route display questions to `../visualization-jupyter/SKILL.md`.

### `POST /heatmap`

```python
payload = {
    'dataset_id': 'gaia',
    'expression_x': 'l',
    'expression_y': 'b',
    'shape_x': 512,
    'shape_y': 256,
    'min_x': 0,
    'max_x': 360,
    'min_y': -90,
    'max_y': 90,
    'filter': None,
    'virtual_columns': {
        'distance': '1/parallax'
    },
}
response = requests.post('http://127.0.0.1:8081/heatmap', json=payload, timeout=30)
assert response.status_code == 200, response.text
heatmap = response.json()
```

POST input model:

```json
{
  "dataset_id": "gaia",
  "expression_x": "l",
  "expression_y": "b",
  "shape_x": 128,
  "shape_y": 128,
  "min_x": null,
  "max_x": null,
  "min_y": null,
  "max_y": null,
  "filter": null,
  "virtual_columns": {}
}
```

## Plot endpoints

Plot endpoints return PNG bytes generated server-side with Matplotlib:

| Endpoint | Method | Input style | Output |
| --- | --- | --- | --- |
| `/histogram.plot/{dataset_id}/{expression}` | GET | Same query fields as histogram GET | PNG image response. |
| `/heatmap.plot/{dataset_id}/{expression_x}/{expression_y}` | GET | Same query fields as heatmap GET plus optional `f` | PNG image response. |

Examples:

```bash
curl -o hist.png 'http://127.0.0.1:8081/histogram.plot/sales/x?min=0&max=100&shape=32'
curl -o heat.png 'http://127.0.0.1:8081/heatmap.plot/sales/x/y?min_x=0&max_x=10&min_y=0&max_y=20&shape_x=32&shape_y=16&f=log1p'
```

Validation:

- Status should be `200`.
- Saved file should be non-empty PNG data.
- If Matplotlib or plotting fails, route plot meaning and headless-display issues to `../visualization-jupyter/SKILL.md`.

## OpenAPI docs

The FastAPI app serves Swagger UI at:

```text
/docs
```

For local debugging only:

```bash
python - <<'PY'
from fastapi.testclient import TestClient
import vaex.server.fastapi as vf
client = TestClient(vf.app)
print(client.get('/docs').status_code)
print(client.get('/openapi.json').status_code)
PY
```

Do not depend on an external public documentation service for verification.

## JavaScript fetch patterns

POST requests are usually easier than long query strings:

```javascript
const input = {
  dataset_id: 'sales',
  expression_x: 'x',
  expression_y: 'y',
  min_x: 0,
  max_x: 10,
  min_y: 0,
  max_y: 20,
  shape_x: 64,
  shape_y: 64,
  filter: null,
  virtual_columns: {}
};
const result = await fetch('http://127.0.0.1:8081/heatmap', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(input)
});
if (!result.ok) {
  throw new Error(await result.text());
}
const data = await result.json();
```

Then hand `centers_x`, `centers_y`, and `values` to a plotting library. Plotting semantics, color scales, orientation, and notebook/frontend handling belong in `../visualization-jupyter/SKILL.md`.
