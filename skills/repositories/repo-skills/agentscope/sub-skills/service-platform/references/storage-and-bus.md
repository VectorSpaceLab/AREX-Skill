# Storage, Message Bus, Workspace, and Hub Wiring

## Purpose

Read this when you need the service-layer components that `create_app` composes.

## Verified component summary

| Component | Verified signature / note |
| --- | --- |
| `InMemoryMessageBus` | Zero-argument local message bus for single-process smoke tests. |
| `RedisMessageBus` | `RedisMessageBus(host='localhost', port=6379, db=0, password=None, connection_pool=None, **kwargs)` |
| `RedisStorage` | `RedisStorage(host='localhost', port=6379, db=0, password=None, connection_pool=None, key_ttl=None, key_config=None, **kwargs)` |
| `AsyncSQLAlchemyStorage` | `AsyncSQLAlchemyStorage(url, *, create_tables=True, auto_migrate=False, engine=None, engine_kwargs=None)` |
| `LocalWorkspaceManager` | `LocalWorkspaceManager(basedir, *, isolation=PER_AGENT, default_mcps=None, skill_paths=None, ttl=3600.0)` |
| `CollectionPerKbManager` | `CollectionPerKbManager(storage, vector_store)` |
| `MCPClient` | `MCPClient(*, name, is_stateful, mcp_config, enable_tools=None, disable_tools=None, execution_timeout=None)` |
| `StdioMCPConfig` | `StdioMCPConfig(*, type='stdio_mcp', command, args=None, env=None, cwd=None, encoding_error_handler='strict')` |
| `HttpMCPConfig` | `HttpMCPConfig(*, type='http_mcp', url, headers=None, timeout=30.0)` |
| `GitHubMCPHub` | `GitHubMCPHub(hub_id='github', display_name='GitHub MCP Registry', description=..., icon_url=..., base_url='https://api.mcp.github.com', api_token=None, timeout=30.0)` |
| `ClawSkillHub` | `ClawSkillHub(hub_id='clawhub', display_name='ClawHub', description=..., icon_url=..., base_url='https://clawhub.ai', api_token=None, timeout=30.0, max_retries=3)` |
| `DiscordChannel` | `DiscordChannel(channel_id, credentials, config)` |
| `FeishuChannel` | `FeishuChannel(channel_id, credentials, config)` |

## Practical notes

- `RedisStorage` and `RedisMessageBus` are the production-style choices when you need multi-process coordination.
- `InMemoryMessageBus` is the safest smoke-test choice.
- `LocalWorkspaceManager` is the easiest way to validate workspace behavior without a remote backend.
- `CollectionPerKbManager` is useful when you want one vector-store collection per knowledge base.
- The example service wires `GitHubMCPHub` and `ClawSkillHub` into the service so the UI can browse external resources.

## Suggested order

1. Verify `storage` and `message_bus` first.
2. Add `workspace_manager`.
3. Add knowledge-base support if the service needs RAG.
4. Add channels or hubs only after the base app starts.
5. Add extra middlewares or extra agent hooks last.
