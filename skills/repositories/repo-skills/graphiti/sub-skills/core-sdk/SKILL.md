---
name: core-sdk
description: "Guides Graphiti Python SDK workflows for ingest, search, backends,
  and custom types."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# core-sdk

Use this sub-skill for the Graphiti Python library itself: building temporal
context graphs, choosing a backend driver, ingesting episodes, searching facts or
nodes, and wiring custom entity or edge types.

## Read first

- `references/api-reference.md` for the verified `Graphiti` API, driver
  constructors, search recipes, and the node/edge objects you will handle.
- `references/workflows.md` for the shortest working paths: quickstart ingest,
  search, custom types, provider selection, and tracing.
- `references/troubleshooting.md` when the SDK import fails, a backend is missing,
  search returns validation errors, or the provider/model setup is unreliable.
- `scripts/quickstart_graphiti.py` for a runnable smoke that adds a few sample
  episodes and prints search results.

## What belongs here

This sub-skill owns the SDK questions people naturally ask directly:

- "How do I create a `Graphiti` instance?"
- "Should I use Neo4j or FalkorDB?"
- "How do I add episodes or bulk episodes?"
- "How do I search facts vs nodes?"
- "How do I customize entity or edge types?"
- "How do I add a single triplet without episode extraction?"
- "How do I summarize a saga or build communities?"
- "How do I use OpenAI-compatible providers, Azure OpenAI, Gemini, or local
  structured-output models?"

## What does not belong here

Route these elsewhere:

- REST route questions, queueing, or Docker deployment -> `sub-skills/rest-service/`
- MCP tool questions, transports, or client integrations -> `sub-skills/mcp-server/`
- Repo maintenance, test policy, or import packaging details -> root references

## Typical workflow

1. Choose the backend driver and credentials.
2. Build indices and constraints.
3. Add one episode or a small batch of episodes.
4. Search with `search()` for facts or `search_()` for nodes and richer recipes.
5. Optionally build communities, summarize a saga, or inspect provenance.
6. Use the bundled quickstart script to confirm the environment.

## API families to remember

- Core client: `Graphiti`
- Drivers: `Neo4jDriver`, `FalkorDriver`
- Search recipes: `NODE_HYBRID_SEARCH_RRF`, `EDGE_HYBRID_SEARCH_RRF`,
  `COMBINED_HYBRID_SEARCH_CROSS_ENCODER`
- Models: `EntityNode`, `EpisodicNode`, `CommunityNode`, `SagaNode`,
  `EntityEdge`, `EpisodicEdge`, `CommunityEdge`, `HasEpisodeEdge`,
  `NextEpisodeEdge`
- Clients: `OpenAIClient`, `OpenAIGenericClient`, `OpenAIEmbedder`,
  `OpenAIRerankerClient`

## Success criteria

A future agent should be able to use this sub-skill to:

- install the right Graphiti package and backend extra,
- create a driver and instantiate `Graphiti`,
- add and search episodes without reopening the original repository,
- choose the right search path or custom-type path,
- and diagnose the predictable import, backend, or provider failure modes.
