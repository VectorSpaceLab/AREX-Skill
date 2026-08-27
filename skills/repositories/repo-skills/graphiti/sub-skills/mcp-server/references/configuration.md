# MCP server configuration

The MCP server loads YAML configuration through `GraphitiConfig`, then applies
environment variables and CLI overrides.

## CLI entry point

Typical module/package entry:

```bash
python main.py --transport http --host 0.0.0.0 --port 8000 --database-provider falkordb
```

Important CLI flags:

- `--config PATH`
- `--transport {http,stdio,sse}`
- `--host HOST`
- `--port PORT`
- `--llm-provider {openai,azure_openai,anthropic,gemini,groq}`
- `--embedder-provider {openai,azure_openai,gemini,voyage}`
- `--database-provider {neo4j,falkordb}`
- `--model MODEL`
- `--small-model MODEL`
- `--temperature FLOAT`
- `--embedder-model MODEL`
- `--group-id GROUP`
- `--user-id USER`
- `--destroy-graph`

## Server and graph sections

Useful YAML shape:

```yaml
server:
  transport: http
  host: 0.0.0.0
  port: 8000

graphiti:
  group_id: default
  episode_id_prefix: ''
  user_id: mcp_user
```

The server default transport is HTTP. `sse` remains supported but is deprecated.
Use `stdio` for desktop-client command integration and `http` for streamable HTTP
clients or container deployments.

## Database section

### Neo4j

```yaml
database:
  provider: neo4j
  neo4j:
    uri: bolt://localhost:7687
    user: neo4j
    password: password
```

### FalkorDB

```yaml
database:
  provider: falkordb
  falkordb:
    host: localhost
    port: 6379
    username: null
    password: null
    database: default_db
```

The MCP Docker docs include two common variants:

- a combined FalkorDB + MCP server container for the simplest local deployment;
- a Neo4j-backed deployment when Neo4j is the system's graph database.

## LLM and embedder sections

Default OpenAI path:

```yaml
llm:
  provider: openai
  model: gpt-4.1-mini
  small_model: gpt-4.1-nano
  temperature: 0.0

embedder:
  provider: openai
  model: text-embedding-3-small
```

Alternative providers are supported by the config schema for LLMs and embedders.
Install the needed provider dependencies before using them.

## Custom entity and edge types

The config schema can define custom entity and edge types as lists of name and
description pairs:

```yaml
graphiti:
  entity_types:
    - name: Person
      description: An individual human referenced in the content
  edge_types:
    - name: WorksFor
      description: Employment or membership of a person in an organization
  edge_type_map:
    - source: Person
      target: Organization
      edge_types: [WorksFor]
```

The server loads those definitions directly into Graphiti's extraction path.
Keep labels and type names valid for the graph backend, and use `Entity` as a
wildcard endpoint when you want an edge type to apply broadly.

## Environment variables

Common environment variables:

- `OPENAI_API_KEY`
- `SEMAPHORE_LIMIT`
- `CONFIG_PATH`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `FALKORDB_URI`, `FALKORDB_HOST`, `FALKORDB_PORT`, `FALKORDB_DATABASE`
- provider-specific model and API-key variables for non-OpenAI providers

## Startup behavior

During initialization the server:

1. loads config and CLI overrides,
2. logs provider/backend/transport choices,
3. optionally clears the graph if `--destroy-graph` is set,
4. initializes a `GraphitiService`,
5. creates a `QueueService`,
6. and starts the requested MCP transport.

Do not use `--destroy-graph` in a shared environment.
