# Optional Dependencies and Credential Boundaries

Many `crewai_tools` exports are thin adapters over optional SDKs, web services, databases, browser runtimes, cloud APIs, or MCP packages. Treat imports, instantiation, and calls as separate safety steps.

## Safe Dependency Workflow

1. Inspect the intended tool class and docs in this skill.
2. Check whether the tool imports optional packages at construction time.
3. Check whether the tool requires environment variables or constructor credentials.
4. Confirm whether using the tool performs network, cloud, browser, database, local process, or file mutation side effects.
5. Prefer keyless local tools or custom deterministic tools when credentials are absent.
6. Ask for approval before installing optional extras, opening network connections, invoking hosted APIs, running browser automation, querying databases, or writing files.

## Installation Patterns

Common install forms:

```bash
pip install 'crewai[tools]'
uv add mcp
uv pip install 'crewai-tools[mcp]'
```

Some tools raise `ImportError` with a specific extra hint when a dependency is missing. For example, web scraping may require packages such as `beautifulsoup4`, and MCP adapter usage requires `mcp`/MCP adapter dependencies.

Do not install extras speculatively. Tie installation to the specific tool the user asked to use.

## Credential Families

| Family | Examples | Typical boundary |
| --- | --- | --- |
| Search/research | Serper, SerpAPI, Brave, Exa, Tavily, Linkup, GitHub | Network search; requires API key or token. |
| Web scraping/browser | Firecrawl, BrightData, Browserbase, Hyperbrowser, Scrapfly, Oxylabs, Stagehand | Network/browser automation; may have paid usage. |
| Cloud/storage | AWS S3, Bedrock agents, Bedrock knowledge base | Cloud credentials, regions, buckets, resource IDs. |
| Databases/vector stores | MySQL, Snowflake, SingleStore, MongoDB, Qdrant, Weaviate, Couchbase, Databricks | Connection strings/tokens; may query private data. |
| Automation/integrations | Composio, Zapier, Apify, MultiOn, CrewAI Platform/Automation, Enterprise Actions | OAuth/API/platform tokens; external actions can mutate systems. |
| AI/ML/sandbox | DALL-E, Vision, E2B, Daytona, Patronus, contextual AI tools | Model/sandbox/eval provider credentials; possible code execution. |
| MCP | `mcp`, `crewai-tools[mcp]`, local server executables, remote MCP URLs | Local process or remote transport; explicit tool filtering and cleanup required. |

## Environment Variable Examples

The tool code uses `EnvVar` declarations and direct environment lookups for variables such as:

- `TAVILY_API_KEY`
- `SERPLY_API_KEY`
- `LINKUP_API_KEY`
- `BROWSERBASE_API_KEY` and `BROWSERBASE_PROJECT_ID`
- `COMPOSIO_API_KEY`
- `ZAPIER_API_KEY`
- `CREWAI_PLATFORM_INTEGRATION_TOKEN`
- `CREWAI_ENTERPRISE_TOOLS_TOKEN`
- AWS-related variables such as region and access keys for S3/Bedrock workflows
- Database-specific host, token, URL, and API key variables

Do not assume this list is exhaustive. Use the tool object's `env_vars` field or the bundled export-listing script for discovery, then ask the user for the specific missing configuration.

## Safe Local Alternatives

When a requested third-party tool cannot run safely:

- Replace search APIs with `FileReadTool`, `DirectoryReadTool`, or a custom tool over user-provided local files.
- Replace remote website scraping with a user-supplied downloaded HTML/text file.
- Replace database tools with a local CSV/JSON snapshot and a deterministic parser.
- Replace hosted automation actions with a dry-run custom tool that validates payload shape but does not send it.
- Replace MCP remote calls with a minimal local stub server only if the user approves local process execution.

## Path and URL Safety

`crewai_tools.security.safe_path` provides path and URL validation used by official tools:

- File paths resolve against an allowed base directory by default.
- Path traversal outside that directory is rejected unless `CREWAI_TOOLS_ALLOW_UNSAFE_PATHS=true` is set.
- Display formatting avoids exposing absolute directory prefixes when possible.
- URLs reject `file://`, non-HTTP schemes, unresolved hostnames, and private/reserved IP addresses by default.

Avoid setting `CREWAI_TOOLS_ALLOW_UNSAFE_PATHS=true` unless the user explicitly requests and accepts the risk.

## Tool Instantiation Warnings

Tool construction itself may perform checks or fail:

- `ScrapeWebsiteTool` requires its HTML parser dependency at construction time.
- Some platform/browser/cloud tools read credentials in `__init__` and raise immediately if absent.
- Enterprise adapters validate token shape and may warn on legacy tokens.
- `MCPServerAdapter` starts the server during initialization, so constructing it can launch a local process or connect to a remote server.

When writing diagnostic code, inspect exports and class metadata without instantiating tools unless explicitly needed.

## Credential Handling Rules

- Keep secrets in runtime environment, secret managers, or user-provided config.
- Pass only the minimum env/header entries needed for a server or tool.
- Do not print headers, tokens, cookies, connection strings, or full local paths.
- Use placeholder names like `runtime_token` in examples, not real-looking tokens.
- Confirm whether the call may incur cost, mutate data, upload files, or expose private data.

## Boundary Links

- LLM provider setup and model API keys: [`llm-and-providers`](../../llm-and-providers/SKILL.md)
- RAG storage, vector stores, and embedding providers: [`memory-knowledge-and-rag`](../../memory-knowledge-and-rag/SKILL.md)
- Crew task assignment and execution control: [`core-runtime`](../../core-runtime/SKILL.md)
