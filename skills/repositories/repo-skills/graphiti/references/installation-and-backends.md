# Installation and backends

Use this reference before running a Graphiti workflow or diagnosing an import/backend
failure.

## Package names and imports

| Surface | Install/import signal | Notes |
| --- | --- | --- |
| Core SDK | install `graphiti-core`, import `graphiti_core` | Exposes `from graphiti_core import Graphiti`. |
| Neo4j backend | base core dependency | Default path when you instantiate `Graphiti(uri, user, password)`. |
| FalkorDB backend | install `graphiti-core[falkordb]` | Provides `graphiti_core.driver.falkordb_driver.FalkorDriver`. |
| REST service | `graph_service.main:app` | FastAPI service surface; see `sub-skills/rest-service/`. |
| MCP server | `graphiti_mcp_server` | MCP transport/tool surface; see `sub-skills/mcp-server/`. |

Minimal public SDK install:

```bash
pip install graphiti-core
# or
uv add graphiti-core
```

FalkorDB support:

```bash
pip install 'graphiti-core[falkordb]'
# or
uv add 'graphiti-core[falkordb]'
```

Optional provider/backend extras are intentionally separate. Install them only when
the workflow actually needs them:

| Extra | When it matters |
| --- | --- |
| `anthropic`, `groq`, `google-genai`, `voyageai` | Alternative LLM/embedder providers. |
| `sentence-transformers` | Local BGE reranker fallback; the model download can be large. |
| `neptune` | Amazon Neptune plus OpenSearch Serverless path. |
| `kuzu` | Deprecated legacy driver; prefer Neo4j or FalkorDB. |
| `falkordblite` | Embedded FalkorDB Lite path on compatible Python versions. |

## First import check

Run this after installing the package in the target environment:

```bash
python -c "from graphiti_core import Graphiti; print(Graphiti.__name__)"
```

For a broader check across the installed core, REST, and MCP surfaces:

```bash
python scripts/check_graphiti_install.py
```

The helper prints installed distribution versions and verifies the public imports
that this skill references.

## Core backend selection

### Neo4j

Neo4j is the default core path. Construct Graphiti directly with connection
credentials:

```python
from graphiti_core import Graphiti

graphiti = Graphiti(
    uri='bolt://localhost:7687',
    user='neo4j',
    password='password',
)
```

Use environment variables in scripts/services:

- `NEO4J_URI` (for example `bolt://localhost:7687`)
- `NEO4J_USER`
- `NEO4J_PASSWORD`
- Optional Neo4j database names are set on `Neo4jDriver(database=...)`.

### FalkorDB

Install the Falkor extra, then pass a driver instance:

```python
from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver

falkor_driver = FalkorDriver(
    host='localhost',
    port=6379,
    username=None,
    password=None,
    database='default_db',
)
graphiti = Graphiti(graph_driver=falkor_driver)
```

Useful environment variables:

- `FALKORDB_HOST`, `FALKORDB_PORT`
- `FALKORDB_USERNAME`, `FALKORDB_PASSWORD`
- `FALKORDB_DATABASE` or `FALKORDB_URI` for the MCP server path

### Neptune

Neptune requires the `neptune` extra plus an Amazon Neptune endpoint and Amazon
OpenSearch Serverless endpoint. Use host prefixes like `neptune-db://...` or
`neptune-graph://...` when constructing `NeptuneDriver`. Treat this as an
explicit cloud-backed workflow, not the default smoke-test backend.

### Kuzu

Kuzu is still represented in code but is deprecated. Use it only for legacy tasks
that explicitly mention Kuzu; do not choose it for new Graphiti work.

## LLM, embedder, and reranker expectations

- The default SDK uses OpenAI-backed LLM, embedder, and reranker clients.
- Set `OPENAI_API_KEY` before ingest/search unless you inject custom clients.
- For local or OpenAI-compatible providers, use `OpenAIGenericClient` and set
  `structured_output_mode='json_object'` if the provider accepts JSON schema
  requests but does not actually enforce them.
- The MCP server's reranker factory tries provider rerankers first. If neither
  the LLM nor embedder provider supplies one, it can fall back to a local BGE
  reranker, which requires `sentence-transformers` and downloads a large model.

## Shared runtime variables

| Variable | Typical use |
| --- | --- |
| `OPENAI_API_KEY` | Default OpenAI LLM/embedder/reranker credentials. |
| `OPENAI_BASE_URL` / provider-specific URL fields | OpenAI-compatible or Azure endpoint routing. |
| `SEMAPHORE_LIMIT` | Limits parallel Graphiti LLM operations; reduce on 429s or local models. |
| `GRAPHITI_TELEMETRY_ENABLED=false` | Disables anonymous telemetry during local checks. |
| `CHUNK_TOKEN_SIZE`, `CHUNK_OVERLAP_TOKENS`, `CHUNK_MIN_TOKENS`, `CHUNK_DENSITY_THRESHOLD` | Advanced entity-dense content chunking controls. |

## Verification expectations

- Import checks prove installation only; they do not prove that a graph database,
  LLM provider, embeddings, or service transport is working.
- A full core smoke needs a live graph backend and API credentials.
- REST and MCP smoke checks need the service process plus whichever backend and
  provider credentials that service config uses.
