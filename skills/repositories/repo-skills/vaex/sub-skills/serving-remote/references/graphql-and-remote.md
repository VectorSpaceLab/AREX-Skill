# GraphQL and Python remote DataFrames

## Python remote DataFrame API

For Python clients, Vaex's remote DataFrame API is usually more convenient than REST. It uses WebSocket messages and exposes a `DataFrameRemote` that supports many ordinary Vaex DataFrame operations while keeping source data on the server.

```python
import vaex

# TLS/WebSocket endpoint through a reverse proxy:
df = vaex.open('vaex+wss://data.example.org/sales')

# Local cleartext loopback endpoint:
df = vaex.open('vaex+ws://127.0.0.1:8081/sales')

# Aggregation returns a compact scalar/grid, not the whole table.
mean_x = df.x.mean()
```

Accepted schemes for `vaex.open` / `vaex.server.connect` include:

| Scheme | Use |
| --- | --- |
| `vaex+ws://` | Cleartext Vaex WebSocket remote DataFrame. Preferred explicit local form. |
| `ws://` | Cleartext WebSocket shorthand accepted by the client. |
| `vaex+wss://` | TLS WebSocket remote DataFrame. Use behind HTTPS/TLS. |
| `wss://` | TLS WebSocket shorthand accepted by the client. |
| `http://` / `vaex+http://` | Recognized by path parsing but HTTP remote DataFrame client is not implemented in this version; use REST endpoints manually instead. |

`vaex.open(url_to_dataset)` splits the last path segment as the dataset name and connects to the server part. For example, `vaex+ws://127.0.0.1:8081/sales` connects to `vaex+ws://127.0.0.1:8081` and returns `client['sales']`.

## `vaex.server.connect`

Use `connect` when you want to inspect or reuse the client object:

```python
import vaex.server

client = vaex.server.connect('vaex+ws://127.0.0.1:8081')
try:
    client.update()
    print(client.df_map.keys())
    df = client['sales']
    print(df.get_column_names())
    print(df.x.mean())
finally:
    client.close()
```

The top-level `vaex.connect(url)` dispatches to `vaex.server.connect(url)`. Use `client.close()` when finished.

## Remote aggregation semantics

Remote DataFrames preserve Vaex's lazy expression model and schedule supported tasks on the server:

```python
df = vaex.open('vaex+ws://127.0.0.1:8081/sales')
df['ratio'] = df.sales / df.visits
selected = df[df.visits > 0]
mean_ratio = selected.ratio.mean()
grid = selected.count(binby=['x', 'y'], limits=[[0, 10], [0, 20]], shape=[32, 16])
```

Operating rules:

- Prefer scalar aggregations, counts, binned grids, and bounded previews.
- Avoid unbounded `df.evaluate(...)`, `.to_pandas_df()`, `.values`, full records, or large row transfer against remote data unless the user explicitly confirms the size.
- Validate remote availability with `df.get_column_names()`, `len(df)`/`df.count()` if affordable, and one compact aggregation.
- If a method is not remote-invokable, reduce the problem to supported expressions/aggregations or run the operation local to the server process.
- For expression syntax, virtual columns, filters, and groupby/binby details, route to `../expressions-analytics/SKILL.md`.

## Tokens and trusted tokens

The WebSocket server path supports `token` and `token_trusted` in the Tornado server/client stack. Token failures usually appear only when an operation is executed, not when a URL string is constructed.

Examples:

```python
# Safer: pass tokens as kwargs instead of embedding in a loggable URL.
df = vaex.open('vaex+ws://127.0.0.1:9000/df', token=TOKEN)

# Also accepted by vaex.open query parsing, but avoid logging this form.
df = vaex.open('vaex+ws://127.0.0.1:9000/df?token=TOKEN')

# Trusted tokens allow more deserialization, including operations that may use pickled functions.
df = vaex.open('vaex+ws://127.0.0.1:9000/df', token_trusted=TRUSTED_TOKEN)
```

Caveats:

- A normal token authorizes ordinary execution.
- A trusted token can allow more dangerous deserialization, such as pickled functions for some `apply`/JIT-like operations. Use only in fully trusted private environments.
- Do not paste real tokens in notebooks, terminal history, issue reports, or skill artifacts.
- If the server was started without tokens but the client sends them, ordinary requests should still work; if the server requires a token and none is sent, expect a `ValueError` like `No token provided, not authorized` during execution.
- `token_trusted` in query strings uses an underscore in the Vaex URL parsing layer.

## FastAPI WebSocket vs legacy Tornado notes

Modern `vaex server` dispatches to the FastAPI app and includes a `/websocket` route. The remote client connects to the base URL plus `/websocket` internally.

The source tree also contains a Tornado `WebServer` stack with explicit `--token`, `--token-trusted`, cache, compression, and thread options. Treat it as behavior evidence for tokens and remote execution, not as the default CLI surface for new instructions. The installed `vaex server --help` option list is the authority for the current console command.

## Optional GraphQL

GraphQL is optional and separate from ordinary REST/WebSocket serving. The GraphQL package exposes Vaex DataFrames through Graphene-style schemas for aggregates, row pagination, filters, and groupby queries.

Install/import expectation:

```bash
python -c "import vaex.graphql, graphene; print('graphql available')"
```

In Python, after `import vaex.graphql`, DataFrames expose a `graphql` accessor:

```python
import vaex
import vaex.graphql

df = vaex.from_arrays(x=[1, 2, 3], y=[10.0, 20.0, 30.0])
result = df.graphql.execute('''
{
  df {
    count
    mean { y }
    min { x }
    max { x }
  }
}
''')
assert not result.errors, result.errors
print(result.data)
```

A GraphQL server can be enabled through `vaex server --graphql` when the installed `vaex-graphql`, Graphene, and Starlette GraphQL integration are compatible. If it is enabled on the FastAPI app, the endpoint is `/graphql`.

GraphQL query shape examples:

```graphql
{
  df {
    count
    min { x }
    mean { y }
    groupby {
      category {
        count
        mean { y }
      }
    }
  }
}
```

```graphql
{
  df(where: {x: {_gt: 4}}) {
    row(offset: 0, limit: 5) { x y }
  }
}
```

Caveats:

- `vaex-graphql` was not required for the serving skill's backend gate. Treat it as optional.
- FastAPI's GraphQL route depends on older Starlette GraphQL APIs in some versions; `ModuleNotFoundError`, missing `starlette.graphql`, or Graphene v2/v3 mismatches are dependency issues.
- Do not start a public listener only to test GraphQL. Prefer an import/schema smoke or a local TestClient if the stack is available.
- If GraphQL fails but `/dataset`, `/histogram`, `/heatmap`, and WebSocket remote checks work, ordinary serving is still usable.
