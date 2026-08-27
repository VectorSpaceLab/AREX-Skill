# LangChain and LangGraph Toolkit

## When to read

Read this when using `wren-langchain` to expose a prepared Wren project as
LangChain/LangGraph tools.

## Initialize

```python
from wren_langchain import WrenToolkit

toolkit = WrenToolkit.from_project("analytics-project", profile=None)
```

The project must have `wren_project.yml` and `target/mdl.json`. An explicit
`profile` selects a named profile; otherwise resolution follows the project then
active-profile behavior.

## Tool and direct APIs

```python
tools = toolkit.get_tools(
    include_memory_write=True,
    raise_on_error=False,
)
prompt = toolkit.system_prompt(tools=tools)

result = toolkit.query("SELECT ...", limit=100)
planned = toolkit.dry_plan("SELECT ...")
toolkit.dry_run("SELECT ...")
```

The runtime tools are `wren_query`, `wren_dry_plan`, and `wren_list_models`.
When memory is enabled, the toolkit can also expose `wren_fetch_context`,
`wren_recall_queries`, and `wren_store_query`.

## Memory write decision

Set `include_memory_write=False` to keep retrieval tools while excluding
`wren_store_query`. Pass the same returned `tools` list to `system_prompt`; this
prevents a prompt from instructing the agent to use a tool that was intentionally
omitted.

## Error behavior and limits

With `raise_on_error=False`, tool failures are serialized into an LLM-readable
success/error envelope. With `raise_on_error=True`, failures propagate to the
host application. LLM-facing query tools use a default limit and enforce a hard
maximum of 1000 rows; aggregate in SQL for larger results.

## Lifecycle note

The toolkit reloads project manifest data per engine construction while caching
its connector for reuse. It is not a profile hot-reload mechanism: construct a
new toolkit after changing profile selection.
