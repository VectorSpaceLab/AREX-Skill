# Memory Workflows

## When to read

Read this for command selection, fallback behavior, or maintenance of an
existing memory index.

## Read schema context

```bash
wren memory describe
wren memory fetch -q "customer order amount"
wren memory fetch -q "order date" --model orders --threshold 0
```

`describe` is a plain-text transformation of the compiled MDL and does not need
semantic embeddings. `fetch` returns full text for smaller schemas and uses
semantic search for larger schemas when the optional memory stack is available.

## Recall and store examples

```bash
wren memory recall -q "best customers" --limit 3
wren memory store --nl "best customers" --sql "SELECT ..."
```

Recall searches durable pair files with the fallback backend; a semantic backend
can improve retrieval. Store writes the durable markdown pair first and indexes
it opportunistically when the optional stack is available.

## Build and maintain the index

```bash
wren memory status
wren memory index
wren memory check
wren memory watch --interval 5
```

- `index` builds semantic schema/query state when the memory extra is present.
  With the grep fallback, it reports that pair files are already directly
  searchable.
- `check` reports drift between durable pair markdown and derived state.
- `watch` is for a project actively changing; it should not compete with other
  work against the same project.
- `reset` drops derived index state but preserves `knowledge/sql/`.

## Migration and management commands

`export` migrates legacy query history into durable markdown pairs. `list`,
`forget`, `dump`, and `load` manage stored pairs. Use them only with a clear
review/change policy: remembered SQL affects future agents.

## Small versus large schema decision

For a small schema, full plain-text context can be clearer than isolated vector
hits. For a large schema, fetch relevant fragments before SQL. Do not re-index
before every question; re-index after source changes or when drift is reported.
