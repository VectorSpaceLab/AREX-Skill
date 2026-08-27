# Example App Recipes

Use these recipes to scaffold user apps from Pydantic AI patterns without relying on original example files. Each recipe names the core shape, the dependencies to plan for, and the sub-skills to read for deeper mechanics.

## General Scaffolding Rules

- Start from an importable Python module with an `Agent` at module scope when the app will be served by `clai --agent`, `clai web --agent`, `uvicorn module:app`, or another process manager.
- Keep provider calls behind explicit model strings and credentials; use `TestModel` or `FunctionModel` for local tests and examples that must be deterministic.
- Store message history using `ModelMessage` objects or `ModelMessagesTypeAdapter` when persistence is required; do not invent ad hoc JSON formats for internal agent messages.
- Put app-specific services such as HTTP clients, database connections, caches, or feature flags into a typed `deps_type` object and pass `deps` per run.
- Treat web servers, databases, Docker, cloud APIs, browser frontends, and external datasets as optional runtime dependencies that must be confirmed with the user before running.

## Minimal Importable Agent

Use this shape when the user needs something `clai --agent module:agent` or `clai web --agent module:agent` can load.

```python
from pydantic_ai import Agent

agent = Agent(
    'openai:gpt-5.2',
    instructions='Answer concisely and ask a follow-up question when requirements are ambiguous.',
)
```

Run with:

```bash
clai --agent assistant_app:agent "Help me plan the migration"
clai web --agent assistant_app:agent -m anthropic:claude-sonnet-4-6
```

Read `../agent-core/SKILL.md` for dependency injection, testing, streaming, and declarative `AgentSpec` alternatives.

## FastAPI Chat App with Stored History

Use this when the user wants a browser or HTTP chat app with persistent conversation history.

Core design:

1. Create one module-scope `Agent`.
2. Create a FastAPI app with lifespan-managed storage, such as SQLite for local development.
3. On `GET /chat`, read saved `ModelMessage` values and serialize only the role/content/timestamp shape needed by the frontend.
4. On `POST /chat`, load stored message history, run `agent.run_stream(prompt, message_history=messages)`, stream newline-delimited JSON chunks to the browser, then persist `result.new_messages_json()`.
5. Keep frontend assets local to the new app, not referenced from source examples.

Important boundaries:

- Use `ModelMessagesTypeAdapter.validate_json(...)` when restoring stored Pydantic AI messages.
- Use `ModelRequest`, `ModelResponse`, `UserPromptPart`, and `TextPart` only after checking part types; route message-format details to `../outputs-and-messages/SKILL.md`.
- Use a thread executor or async database driver for blocking storage calls inside async routes.
- Configure Logfire as optional (`send_to_logfire='if-token-present'`) if observability is useful, but do not require it for local app startup.

## Built-in Web Chat UI

Use this when the user wants the quickest local browser UI around an existing agent and not a custom frontend.

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')
app = agent.to_web(models={'Claude': 'anthropic:claude-sonnet-4-6'})
```

Run with:

```bash
uvicorn assistant_app:app --host 127.0.0.1 --port 7932
```

Choose `clai web` instead when no Python app file is needed. Choose UI event stream adapters or AG-UI when the user is integrating with a production frontend or custom event protocol.

## Structured Extraction App

Use this when the app converts free text into a Pydantic model.

Core design:

1. Define a `BaseModel` output type with field descriptions.
2. Create `Agent(model, output_type=YourModel)`.
3. Accept a prompt from CLI, HTTP, queue, or batch input.
4. Run the agent and persist or return `result.output.model_dump()`.
5. Add a deterministic unit test using `TestModel(custom_output_args=...)` rather than a live provider.

Route detailed output-mode choices to `../outputs-and-messages/SKILL.md`.

## Weather or Multi-Tool Service App

Use this when the user needs a tool-calling service backed by external HTTP APIs.

Core design:

1. Define a typed dependency object containing an `httpx.AsyncClient` and any service settings.
2. Create `Agent(..., deps_type=Deps, retries=2, instructions='Be concise...')`.
3. Register tools with `@agent.tool` when they need `RunContext[Deps]`.
4. Validate external API responses with Pydantic models before returning values to the agent.
5. In app startup, create the HTTP client; in shutdown, close it.
6. In tests, replace network tools with deterministic functions or use `Agent.override(model=TestModel())`.

External API keys such as weather or geocoding credentials should be optional when the app can fall back to dummy data; otherwise fail fast with a clear missing-configuration error.

## SQL Generation App

Use this when the user asks for a natural-language-to-SQL assistant.

Core design:

1. Keep the database schema and a few safe example requests in the agent instructions.
2. Define a union output such as `Success(sql_query, explanation)` or `InvalidRequest(error_message)`.
3. Use an output validator to reject non-`SELECT` statements and run `EXPLAIN` against a database connection stored in deps.
4. Raise `ModelRetry` with the database error when validation fails so the model can correct the query.
5. Run only against a constrained development database or read-only database role.

This recipe requires a database service. Do not start Docker or connect to a real database without user confirmation.

## RAG App

Use this when the user needs retrieval over documents before answering.

Core design:

1. Define a document ingestion job that chunks source content and stores embeddings plus metadata.
2. Store vector data in a chosen backend such as pgvector, a local vector store, or a managed database.
3. Put database and embedding clients into deps.
4. Register a retrieval tool that accepts the user's query, performs vector search, and returns compact source snippets.
5. Make the agent answer only from retrieved snippets when grounding is required.
6. Separate costly embedding build steps from online query handling.

RAG examples often require provider embedding credentials and a database. Treat ingestion as a separate, explicitly authorized operation because it may make many provider calls.

## Data Analyst App

Use this when the agent should reason over query results without seeing every row.

Core design:

1. Put a dataframe, DuckDB connection, or query service into deps.
2. Register one tool that runs constrained queries and stores the full result in deps or a side channel.
3. Return only a compact schema, row count, sample, or summary to the model.
4. Register follow-up tools that operate on the stored result when the model needs transformations or charts.
5. Guard query inputs and file paths; do not let a model execute arbitrary SQL against sensitive data.

Route tool safety and schema design to `../tools-and-toolsets/SKILL.md`.

## Streaming Markdown CLI App

Use this when the user wants a terminal command that streams markdown output.

Core design:

1. Create an agent with a provider-prefixed model.
2. Use `async with agent.run_stream(prompt) as result`.
3. Iterate `result.stream_output(...)` and render text chunks with a terminal library.
4. Fall back to non-streaming output when terminal rendering or provider streaming is unavailable.

For an existing agent, prefer `Agent.to_cli()` unless the app needs custom rendering, command parsing, or side effects.

## AG-UI Backend

Use this when a frontend speaks the AG-UI protocol.

Core design:

1. Build the backend as an ASGI app using Pydantic AI's AG-UI adapter.
2. Separate server-side Pydantic AI tools from client-side AG-UI tools.
3. Model shared UI state with Pydantic models before using it in instructions or tools.
4. Treat human-in-the-loop approvals as protocol events, not as normal terminal input.
5. Keep browser/frontend setup outside this CLI sub-skill; route protocol and adapter details to `../mcp-and-integrations/SKILL.md`.

AG-UI examples commonly require an external JavaScript frontend and provider credentials. Do not assume that frontend is installed.

## Running Installed Examples Safely

If the user explicitly asks to run installed examples, first check:

1. `pydantic_ai_examples` imports.
2. Required optional extras are installed.
3. Required provider credentials are present.
4. Required services such as PostgreSQL, pgvector, browser frontend, Docker, or external APIs are available and authorized.
5. The example does not make costly or credentialed calls unexpectedly.

Use this command shape only for installed examples:

```bash
python -m pydantic_ai_examples.pydantic_model
```

Do not instruct future agents to run source-tree example paths. If an example is not installed or has unsafe prerequisites, scaffold a local recipe using the patterns above instead.
