# Core SDK workflows

## Quickstart ingest and search

Use this path when you need a minimal working graph.

1. Install the SDK and the backend extra you need.
2. Set `OPENAI_API_KEY` or inject custom LLM/embedder/reranker clients.
3. Choose a backend driver.
4. Call `build_indices_and_constraints()`.
5. Add text or JSON episodes with `add_episode()`.
6. Call `search()` for facts and `search_()` for nodes/communities.
7. Close the client.

The bundled helper performs those steps for a tiny fixed dataset:

```bash
python scripts/quickstart_graphiti.py --backend neo4j
python scripts/quickstart_graphiti.py --backend falkordb
```

The helper intentionally uses a fresh `group_id` by default so it does not clear or
mutate existing groups.

## Backend patterns

### Neo4j

```python
from graphiti_core import Graphiti

graphiti = Graphiti('bolt://localhost:7687', 'neo4j', 'password')
await graphiti.build_indices_and_constraints()
```

Use Neo4j for default/core development and for local hybrid-search workflows that
need reliable concurrent query behavior.

### FalkorDB

```python
from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver

driver = FalkorDriver(host='localhost', port=6379, database='default_db')
graphiti = Graphiti(graph_driver=driver)
await graphiti.build_indices_and_constraints()
```

Use FalkorDB for the repo's alternative backend path and for MCP deployments that
use the combined FalkorDB container.

## Add episodes

Use `EpisodeType.text`, `EpisodeType.json`, or `EpisodeType.message`.
When adding JSON, pass a JSON string as `episode_body` rather than a raw Python
object unless you explicitly serialize it in the call.

```python
import json
from datetime import datetime, timezone
from graphiti_core.nodes import EpisodeType

await graphiti.add_episode(
    name='Customer Profile',
    episode_body=json.dumps({'name': 'Alice', 'role': 'Engineer'}),
    source=EpisodeType.json,
    source_description='CRM data',
    reference_time=datetime.now(timezone.utc),
    group_id='customer-graph',
)
```

## Search facts vs nodes

Use `search()` when you want fact/relationship answers:

```python
facts = await graphiti.search('Who works at Acme?', group_ids=['customer-graph'])
for edge in facts:
    print(edge.fact)
```

Use `search_()` with a node recipe when you need entity nodes:

```python
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF

config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
config.limit = 5
results = await graphiti.search_('Acme employees', config=config, group_ids=['customer-graph'])
for node in results.nodes:
    print(node.name, node.labels)
```

Use a center node UUID when you want graph-distance-aware reranking:

```python
facts = await graphiti.search('Acme', center_node_uuid=some_node_uuid)
```

## Custom entity and edge types

Define Pydantic models and pass them into `add_episode()`:

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    """A human person."""
    role: str | None = Field(default=None, description='Work role when known')

class WorksFor(BaseModel):
    """Employment or affiliation fact."""

await graphiti.add_episode(
    name='Work note',
    episode_body='Alice is a backend engineer at Acme.',
    source_description='note',
    reference_time=now,
    entity_types={'Person': Person},
    edge_types={'WORKS_FOR': WorksFor},
    edge_type_map={('Person', 'Entity'): ['WORKS_FOR']},
)
```

Use `excluded_entity_types` when the task needs to prevent specific configured
types from being extracted. Keep the exclusion list limited to `Entity` or names
present in your `entity_types` mapping.

## Context and saga controls

- Use `previous_episode_uuids` to supply explicit context rather than relying on
  automatic recent-episode retrieval.
- Use `saga` and `saga_previous_episode_uuid` to group ordered episodes.
- Use `summarize_saga()` after saga ingest to refresh its summary.
- Use `get_nodes_and_edges_by_episode()` to trace provenance from episodes to
  created nodes and facts.

## Direct triplets

Use `add_triplet()` when the fact is already known and you want to bypass LLM
extraction:

```python
from datetime import datetime, timezone
from graphiti_core.nodes import EntityNode
from graphiti_core.edges import EntityEdge

now = datetime.now(timezone.utc)
source = EntityNode(name='Alice', group_id='team', created_at=now)
target = EntityNode(name='Acme', group_id='team', created_at=now)
edge = EntityEdge(
    name='WORKS_FOR',
    fact='Alice works for Acme.',
    group_id='team',
    source_node_uuid=source.uuid,
    target_node_uuid=target.uuid,
    created_at=now,
)
await graphiti.add_triplet(source, edge, target)
```

## Provider and local-model paths

- Official OpenAI: default clients are usually enough once `OPENAI_API_KEY` is set.
- Azure OpenAI: use Azure-compatible OpenAI clients and deployment names for both
  LLM and embedding models.
- Gemini: configure LLM, embedder, and reranker clients together when using Gemini
  for all components.
- OpenAI-compatible/local endpoints: use `OpenAIGenericClient` and an
  `OpenAIEmbedder` pointed at the provider's `/v1` endpoint. Prefer
  `structured_output_mode='json_object'` for providers that do not enforce JSON
  schema output.
- If provider reranking is unavailable, decide whether the local BGE reranker and
  its heavy dependency/model download are acceptable.

## Tracing and telemetry

- Pass a tracer into `Graphiti(..., tracer=..., trace_span_prefix='...')` for
  OpenTelemetry spans.
- Set `GRAPHITI_TELEMETRY_ENABLED=false` during local checks if you do not want
  anonymous telemetry.

## Validation checklist

Before declaring a core workflow ready:

- Import `graphiti_core` from the intended environment.
- Confirm the graph backend is reachable.
- Confirm model credentials or custom clients are configured.
- Add data into a unique `group_id` unless intentional reuse is required.
- Run both a fact search and, when appropriate, a node search.
- Close the `Graphiti` client.
