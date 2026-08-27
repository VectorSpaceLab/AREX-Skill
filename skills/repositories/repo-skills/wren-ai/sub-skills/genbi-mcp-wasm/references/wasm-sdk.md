# Browser WASM SDK

## When to read

Read this when a browser application, static dashboard, or client-side agent
needs MDL-aware queries over static/registered data.

## Install and initialize

```javascript
import { WrenEngine } from '@wrenai/wren-core-wasm';

const engine = await WrenEngine.init();
```

Use the published package or a compatible bundler. The WebAssembly binary is
large, so show a loading state and ensure the bundler copies it. For CDN use,
prefer unpkg; jsDelivr has a file-size limit that can block the binary.

## Register data, then load MDL

```javascript
await engine.registerJson('orders', [
  { id: 1, customer: 'Alice', amount: 150 },
]);
await engine.loadMDL(mdl, { source: '' });
const rows = await engine.query('SELECT customer, SUM(amount) AS total FROM Orders GROUP BY 1');
engine.free();
```

Available registration methods:

```typescript
engine.registerJson(name, rows)
engine.registerCsv(name, textOrBytes, options?)
engine.registerParquet(name, bytes)
engine.loadMDL(mdl, { source })
engine.query(sql)
engine.cubeQuery(input)
engine.listCubes()
engine.free()
```

## Source modes

| `source` value | Behavior |
| --- | --- |
| HTTP/HTTPS prefix | URL mode; models resolve to remote Parquet under the prefix |
| empty string | auto-detect; non-URL models must already be registered |
| any other nonempty string | strict local mode; missing registered models fail at `loadMDL` |

Use strict local mode to catch missing table registration before query time.
URL mode can collide when several models share a bare physical table name.

## CSV options and cube queries

CSV options include `header`, `delimiter`, `quote`, `escape`, `terminator`,
`batchSize`, `inferRows`, and an optional explicit schema. For aggregations,
call `listCubes()` after loading MDL and prefer `cubeQuery()` with a structured
object containing cube, measures, optional dimensions/timeDimensions/filters,
limit, and offset.

## Runtime constraints

- Queries execute in the browser and materialize registered inline data in
  memory.
- The engine is single-threaded; long queries can block the main thread.
- Use remote Parquet URL mode for larger data rather than loading everything
  into a browser tab.
- There is no Wren semantic-memory/toolkit layer in this runtime.
