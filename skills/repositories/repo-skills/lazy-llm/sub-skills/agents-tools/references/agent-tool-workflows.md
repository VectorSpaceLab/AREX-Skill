# Agent and Tool Workflows

## Deterministic tool registration first

Register and inspect a tool before putting it behind an LLM agent.

```python
import lazyllm
from lazyllm.tools import fc_register

@fc_register("tool", execute_in_sandbox=False)
def add_one(x: int):
    """Return x + 1."""
    return x + 1

tool = lazyllm.tool.add_one()
assert tool.execute_in_sandbox is False
```

Use the bundled [tool_agent_smoke.py](../scripts/tool_agent_smoke.py) for a safe metadata check.

## Tool metadata decisions

| Metadata | Use when | Caveat |
| --- | --- | --- |
| `execute_in_sandbox=False` | The tool is safe and must run outside the configured sandbox | Default is true; be explicit when disabling. |
| `input_files_parm="name"` | A tool accepts an input file path parameter | Validate paths and avoid reading secrets. |
| `output_files_parm="name"` | A tool writes to a path parameter | Do not overwrite user files without approval. |
| `output_files=[...]` | A tool has known static output paths | Keep outputs under approved workspaces. |
| `rewrite_func` | The public tool wrapper should differ from the underlying callable | Check function name/schema after rewriting. |

## Choosing an agent class

- **ReactAgent**: choose for iterative tool use with retries and optional last-tool-call return.
- **ReWOOAgent**: choose when planning and observations should be separated before solving.
- **PlanAndSolveAgent**: choose when planning and solving roles may use separate LLMs.

All real agent runs need an LLM module. Configure that through model-deployment and keep tool registration checks separate from LLM/provider execution.

## Tool categories

- **Pure Python tools**: safest for local tests; use them for schema and agent skeleton checks.
- **Shell/sandbox tools**: may read/write files or run commands; require workspace and sandbox policy.
- **HTTP/search tools**: network and provider limits apply; preserve response contracts and timeouts.
- **SQL manager tools**: use temp/local databases for tests; require approval for production connections.
- **Writer tools**: route artifact schemas and writer-specific behavior to writer-review.
- **RAG tools**: route document/retrieval setup to rag-document-processing.

## Agent construction sequence

1. Write deterministic tools with docstrings and type hints.
2. Register tools and inspect metadata.
3. Validate each tool independently with tiny inputs.
4. Configure the LLM/provider/backend.
5. Instantiate the agent with explicit `tools`, `skills`, `workspace`, `sandbox`, and trace/stream options.
6. Run a no-side-effect prompt first; only then enable external tools.

## Native verification candidates

Safe or mostly local tests include agent base/events, built-in tool metadata, dynamic toolkit, HTTP node contract, ReWOO skeleton behavior, search content contracts, SQL manager with local DB, sandbox metadata, skills management, and tool-manager concurrency. Provider-backed or MCP-process tests remain optional.
