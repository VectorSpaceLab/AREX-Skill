# LEANN CLI reference

This catalog reflects the installed `leann` parser. Put global verbosity flags
**before** the command group:

```bash
leann [--verbose | --quiet] GROUP ...
```

`-v`/`--verbose` exposes native FAISS/HNSW output. `-q`/`--quiet` is accepted,
but native output is already suppressed by default. `--verbose` and `--quiet`
are mutually exclusive.

## Inventory: all 19 groups

| Group | Purpose | Required positionals |
|---|---|---|
| `build` | Build or update a document index | optional `index_name` |
| `watch` | Poll stored source scope and rebuild on change | `index_name` |
| `migrate-ids` | Rewrite passage IDs to content hashes | `index_name` |
| `rebuild` | Replay stored build configuration | `index_name` |
| `search` | Semantic retrieval | `index_name query` |
| `warmup` | Start/warm an embedding server | `index_name` |
| `daemon` | Start, stop, or inspect embedding daemons | nested action |
| `ask` | Retrieve and answer with an LLM | `index_name`, optional `query` |
| `react` | Multi-iteration retrieval agent | `index_name query` |
| `index-browser` | Index Chrome or Brave history | optional `chrome|brave` |
| `index-email` | Index Apple Mail | none |
| `index-calendar` | Index Apple Calendar | none |
| `index-imessage` | Index iMessage | none |
| `index-wechat` | Index exported WeChat JSON | `--export-dir` |
| `index-chatgpt` | Index a ChatGPT export | `--export-path` |
| `index-claude` | Index a Claude export | `--export-path` |
| `list` | Discover local and registered indexes | none |
| `remove` | Remove one resolved index | `index_name` |
| `serve` | Start the optional HTTP service | none |

Use `leann GROUP --help`; for daemon actions, use
`leann daemon {start,stop,status} --help`.

## `build`

```text
leann build [index_name] [--docs PATH [PATH ...]]
  [--backend-name {hnsw,diskann,ivf}]
  [--embedding-model MODEL]
  [--embedding-mode {sentence-transformers,openai,mlx,ollama}]
  [--embedding-host URL] [--embedding-api-base URL]
  [--embedding-api-key KEY] [--embedding-batch-size N]
  [--embedding-prompt-template TEXT] [--query-prompt-template TEXT]
  [--force]
  [--graph-degree N] [--complexity N] [--num-threads N]
  [--compact|--no-compact] [--recompute|--no-recompute]
  [--file-types EXTENSIONS] [--include-hidden|--no-include-hidden]
  [--doc-chunk-size N] [--doc-chunk-overlap N]
  [--code-chunk-size N] [--code-chunk-overlap N]
  [--use-ast-chunking] [--ast-chunk-size N] [--ast-chunk-overlap N]
  [--ast-fallback-traditional]
  [--id-scheme {sequential,content-hash}]
```

Defaults: index name is the current directory basename; `--docs` is `.`;
backend is HNSW; compact is off; recomputation is on; document chunks are
256 tokens plus 128-token overlap; code chunks are 512 tokens plus 50-token
overlap; AST chunks are 300 non-whitespace characters plus 64-character
overlap; ID scheme is `sequential`. The embedding-model default is selected at
runtime: `BAAI/bge-base-en-v1.5` on detected NVIDIA CUDA, otherwise
`sentence-transformers/all-MiniLM-L6-v2`.

`--file-types` is one comma-separated value such as `.md,.py`; it is not a
space-separated list. `--docs` may mix files and directories. Overlap values at
or above their chunk size are reduced to `size - 1` by the CLI. Use
[the lifecycle guide](index-lifecycle-operations.md) before `--force`.

Prompt behavior:

- only `--embedding-prompt-template`: one legacy prompt applies to embeddings;
- both build and query templates: they are stored separately and replayed by
  `rebuild`;
- never add a task prefix unless the selected embedding model requires it.

Do not put secrets in command history. A key supplied by
`--embedding-api-key` or resolved from the embedding provider environment can
be persisted in index metadata by the current build path, so protect the index
as sensitive data. Provider setup and credential handling belong in
[embeddings and chat](../../embeddings-and-chat/SKILL.md).

## `search`

```text
leann search index_name query
  [--top-k N] [--complexity N] [--beam-width N] [--prune-ratio R]
  [--recompute|--no-recompute]
  [--pruning-strategy {global,local,proportional}]
  [--json] [--non-interactive] [--show-metadata]
  [--embedding-prompt-template TEXT]
  [--daemon|--no-daemon] [--daemon-ttl SECONDS]
  [--warmup|--no-warmup]
  [--metadata-filters JSON_OBJECT]
```

Defaults are top-k 5, complexity 64, beam width 1, prune ratio 0, global
pruning, recomputation on, daemon reuse on, daemon TTL 900 seconds, and warmup
on. `--json` emits an array with `id`, `score`, `text`, and `metadata`; combine
it with `--non-interactive` in automation so duplicate index names never cause
a prompt. Index-resolution diagnostics are redirected to stderr in JSON mode.

The query is positional: use `leann search notes "question"`, not `--query`.
`--metadata-filters` must decode to an object:

```bash
leann search notes "deployment" \
  --metadata-filters '{"chapter":{"<=":5},"genre":{"==":"fiction"}}'
```

All fields are combined with AND. Operators are `==`, `!=`, `<`, `<=`, `>`,
`>=`, `in`, `not_in`, `contains`, `starts_with`, `ends_with`, `is_true`, and
`is_false`; `in`/`not_in` require a JSON array. Filtering is applied after
candidate retrieval, so raise `--top-k` if selective filters return too few
items.

There are **no** `--grep`, `--hybrid`, or BM25 switches in this CLI parser.
Use the Python API workflows in [API and indexing](../../api-and-indexing/SKILL.md)
for pure grep, BM25, or hybrid fusion. Do not invent CLI flags from Python
method names.

## `ask` and `react`

```text
leann ask index_name [query]
  [--llm {simulated,ollama,hf,openai,anthropic,minimax,novita,atlascloud,atlas-cloud,atlas}]
  [--model MODEL] [--host URL] [--interactive]
  [--top-k N] [--complexity N] [--beam-width N] [--prune-ratio R]
  [--recompute|--no-recompute]
  [--pruning-strategy {global,local,proportional}]
  [--thinking-budget {low,medium,high}]
  [--api-base URL] [--api-key KEY]
  [--metadata-filters JSON_OBJECT]

leann react index_name query
  [--llm PROVIDER] [--model MODEL] [--host URL]
  [--top-k N] [--max-iterations N]
  [--api-base URL] [--api-key KEY]
  [--serper-api-key KEY] [--jina-api-key KEY]
```

`ask` defaults to Ollama `qwen3:8b`, top-k 20, complexity 32, and interactive
off. With neither a positional query nor `--interactive`, it prompts once.
With both a query and `--interactive`, it answers the query first and then
starts the loop. Interactive commands are `help`, `history`, `clear`, and
`quit`/`exit`/`q`; history is stored per index when readline is available.
Metadata-filter validation happens before chat startup.

`react` defaults to top-k 5 and five iterations. It can use local retrieval
without web keys; Serper enables web search and Jina enables page fetching.
Provider behavior, credentials, model aliases, and thinking-budget semantics
belong in [embeddings and chat](../../embeddings-and-chat/SKILL.md).

## Warmup and daemon

```text
leann warmup index_name
  [--daemon|--no-daemon] [--daemon-ttl SECONDS]
  [--warmup|--no-warmup]

leann daemon start index_name
  [--daemon-ttl SECONDS] [--warmup|--no-warmup]
leann daemon stop [index_name] [--all]
leann daemon status [index_name]
```

Defaults are daemon mode on, TTL 900 seconds (`0` means no expiry), and warmup
on. `daemon stop` requires an index name unless `--all` is supplied. See
[daemon, watch, and registry](daemon-watch-and-registry.md) for process and port
behavior.

## Watch, migration, and rebuild

```text
leann watch index_name [--interval SECONDS] [--once] [--dry-run]
leann migrate-ids index_name [--dry-run] [--yes]
leann rebuild index_name [--force]
```

Watch defaults to a 30-second poll. `--once` performs one comparison;
`--dry-run` reports without rebuilding. Migration is irreversible and may
deduplicate identical text; perform the documented backup first. Rebuild is an
idempotent delta by default and full with `--force`. See
[index lifecycle operations](index-lifecycle-operations.md).

## Personal-data indexers

All seven indexers accept:

```text
[--index-name NAME] [--embedding-model MODEL]
[--embedding-mode {sentence-transformers,openai,mlx,ollama}]
[--embedding-host URL] [--embedding-api-base URL]
[--embedding-api-key KEY] [--embedding-batch-size N]
[--max-count N] [--no-recompute]
```

Their default embedding model is `facebook/contriever`; default maximum count
is 1000. They build a local HNSW index. Specific forms are:

```text
leann index-browser [chrome|brave] [...common options]
leann index-email [...common options]
leann index-calendar [...common options]
leann index-imessage [...common options]
leann index-wechat --export-dir DIRECTORY [...common options]
leann index-chatgpt --export-path PATH [...common options]
leann index-claude --export-path PATH [...common options]
```

The macOS indexers and export prerequisites are summarized in
[daemon, watch, and registry](daemon-watch-and-registry.md). Deep extraction and
reader behavior belongs in [RAG applications](../../rag-applications/SKILL.md).

## Registry, removal, and HTTP service

```text
leann list [--max-depth N]
leann remove index_name [--force]
leann serve [--host HOST] [--port PORT]
```

`list` defaults to app-index scan depth 5. `remove --force` skips confirmation
only when exactly one match exists; it refuses to choose among duplicate names.
`serve` defaults to `127.0.0.1:8000` and requires optional server dependencies.
HTTP endpoints and deployment belong in
[MCP and services](../../mcp-and-services/SKILL.md).

## Bundled non-executing planner

[`../scripts/build_leann_command.py`](../scripts/build_leann_command.py) prints
one shell-quoted command and never runs it. Its global helper option
`--check-inputs` verifies build/export input paths. It intentionally does not
accept secret-bearing `--embedding-api-key`, `--api-key`, `--serper-api-key`,
or `--jina-api-key`; configure secrets only when executing the printed command.
It also omits grep/hybrid because those are not CLI groups or flags.

The planner preserves all other flags listed by its own `--help`, normalizes
metadata JSON, rejects unknown filter operators, requires arrays for `in` and
`not_in`, and applies stricter safe validation to positive counts, ratios,
TTLs, and ports. Put its global options before its group:

Resolve the linked script to `PLANNER`; then it can be invoked from any working
directory, and relative input paths are checked against that directory:

```bash
python3 "$PLANNER" --check-inputs build notes \
  --docs ./README.md ./src --file-types .md,.py
```
