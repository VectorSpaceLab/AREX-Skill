# Wren MCP Server

## When to read

Read this when exposing an already prepared Wren project to an MCP-compatible
client.

## Preconditions

- The project has a current `target/mdl.json`.
- Install the optional server dependency:
  ```bash
  pip install "wrenai[mcp]"
  ```
- A profile is needed for execution tools unless `--no-connect` is selected.

## Start modes

```bash
# Client spawns this process over standard input/output.
wren serve mcp

# Local Streamable HTTP endpoint.
wren serve mcp --transport http --host 127.0.0.1 --port 8080
```

Use `--project` to choose a project explicitly and `--profile` to select a
profile. Startup emits client-registration guidance unless `--quiet` is used.

## Capability boundary

| Option | Effect |
| --- | --- |
| default | query, planning, schema, and knowledge tools as permitted by the project/profile |
| `--no-connect` | disables `run_sql`, `dry_run`, and `query_cube`; retains planning/context surfaces |
| `--allow-write` | registers `store_query` in addition to read-only knowledge tools |

The server supplies query tools such as `run_sql`, `dry_run`, `dry_plan`, and
`query_cube`; schema tools such as `get_mdl`, `list_models`, and `describe_model`;
and knowledge tools such as instructions, context, recall, schema description,
and stored-pair access. It also supplies project/knowledge resources and a Wren
workflow prompt.

## Security model

Connection details are resolved server-side at startup. SQL/results and metadata
cross the MCP boundary; credentials should not. HTTP binds to loopback by
default and has no built-in bearer-token design here, so use an external network
and authentication design before exposing it beyond a trusted local environment.

The server warns when project source files are newer than the compiled MDL. It
does not silently rebuild; run `wren context build` deliberately.
