# MCP, Memory, Privacy, and JSON Plugins

Read this for common state/tool/data-format plugins.

## MCP plugin

The MCP plugin connects OptiLLM to Model Context Protocol servers and exposes tools/resources/prompts to the model.

### Config shape

Default config location is `~/.optillm/mcp_config.json`. A minimal shape is:

```json
{
  "mcpServers": {
    "filesystem": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"],
      "env": {},
      "description": "Local filesystem access"
    }
  },
  "log_level": "INFO"
}
```

Transports:

- `stdio`: local command with args/env.
- `sse`: remote Server-Sent Events URL plus headers.
- `websocket`: remote WebSocket URL.

Headers and string values can expand environment variables using `${NAME}`.

### MCP safety

- Only configure trusted servers.
- Restrict filesystem/server scopes.
- Treat tool calls as side-effecting unless the server documentation proves read-only behavior.
- Current repo code expects MCP APIs including websocket client support; if `mcp.client.websocket` import fails, use an MCP package version below `2` or update the plugin code.

## Memory plugin

The memory plugin chunks long context, extracts key information, stores margin notes, retrieves relevant items, and uses them in a final response.

- Default memory is in-process only.
- Set `OPTILLM_MEMORY_FILE` to persist items across requests.
- The `Memory` class tolerates missing, corrupt, or wrong-shaped JSON files by starting with an empty store.
- Loaded memory respects `max_size`, keeping recent items.

Use file persistence only in a secure path. Memory files can contain user content.

## Privacy plugin

The privacy plugin uses Presidio analyzer/anonymizer behavior to replace PII before provider calls and restore it afterward.

Typical failure surfaces:

- Missing Presidio or spaCy dependencies.
- Analyzer model/resource downloads or initialization latency.
- Text that contains entities not recognized by configured recognizers.
- Logs capturing text before anonymization.

Use privacy when the provider should not see raw PII, but do not treat it as a complete data governance system. Keep prompts/logs/configs under normal sensitive-data handling.

## JSON plugin

The JSON plugin uses `response_format` schema data and outlines/transformers/Pydantic machinery to generate structured JSON.

### Request shape

```python
client.chat.completions.create(
    model="json-gpt-4o-mini",
    messages=[{"role": "user", "content": "Return a city record."}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "city",
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "population": {"type": "integer"}},
                "required": ["name"]
            }
        }
    }
)
```

### JSON cautions

- The plugin can initialize a HuggingFace model through outlines; that may download weights unless already cached.
- Schema conversion maps basic JSON schema types to Pydantic fields; complex schemas may need simplification.
- If the user only needs provider-native JSON mode, direct provider pass-through may be cheaper than the plugin.
- Test with a tiny schema before using a production schema.

## Combined use examples

- `privacy&json-model`: anonymize prompt before structured output generation.
- `memory&moa-model`: retrieve long-context notes before a multi-agent approach.
- `mcp-model`: expose configured MCP tools to the model.

Check cost and side effects before combining plugins with multi-call approaches.
