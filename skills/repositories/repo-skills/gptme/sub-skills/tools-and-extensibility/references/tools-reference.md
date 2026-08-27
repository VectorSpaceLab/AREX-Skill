# gptme tools reference

This reference is for operating an installed gptme tool runtime. It is self-contained; use [../scripts/list_gptme_tools.py](../scripts/list_gptme_tools.py) to confirm the exact tools and availability in the target environment.

## Built-in tool catalog and selection patterns

The package discovers tools as `ToolSpec` instances and then filters them through the active allowlist. The exact set can change with installation extras, configured plugin paths, and MCP configuration, so treat this table as the baseline catalog and verify live.

| Category | Tools | Typical use | Caveats |
| --- | --- | --- | --- |
| File operations | `read`, `save`, `append`, `patch`, `patch_many`, `morph`, `view_anchored`, `hashline_edit`, `patch_anchored` | Read files, create or overwrite files, apply patches, use anchored edits, or use Morph Fast Apply. | `save`, `append`, patch tools, and Morph can modify files. Morph depends on optional configuration/service availability. Anchored/hashline variants may be disabled by default and should be explicitly allowed when needed. |
| Code execution | `shell`, `ipython`, `tmux` | Run shell commands, Python REPL code, and long-running terminal sessions. | High side-effect surface. Use minimal allowlists for untrusted workspaces. `tmux` requires the `tmux` binary. |
| Web/research | `browser`, `rag`, `chats`, `gh` | Browse/read URLs and PDFs, search/index local docs, search conversation history, query GitHub through `gh`. | `browser` needs Playwright or Lynx. `rag` and `gh` may need optional dependencies, indexes, CLI auth, or network. Provider credentials and model routing are outside this sub-skill. |
| Visual/desktop | `vision`, `screenshot`, `computer` | Attach/view images, capture a screen, or control a desktop. | `screenshot` and `computer` need host GUI/system dependencies. Treat desktop automation as opt-in and sensitive. |
| User interaction | `choice`, `elicit`, `form`, `clarify`, `complete`, `progress`, `restart` | Collect structured user input, signal subagent/automation status, finish or restart a session. | Many signal tools are disabled by default and loaded only for autonomous/subagent/server contexts. |
| Workflow awareness | `todo`, `lessons`, `autocommit`, `precommit`, `autocompact`, `vent` | Track in-session work, include contextual lessons, prompt commits/checks, compact large sessions, or record friction. | `precommit` needs a checkout with pre-commit installed/configured. `autocommit` prompts rather than committing by itself. |
| Delegation | `subagent` | Spawn isolated or restricted child agents, fan out batches, wait/cancel/read child logs. | Use explicit profiles and worktree isolation for write-capable subagents. See the subagent section below. |
| Extension bridge | `mcp` | Discover, load, and manage MCP servers from a conversation. | MCP servers run as external processes or HTTP services with their own trust boundary. See [mcp-browser-computer.md](mcp-browser-computer.md). |

Use inventory output rather than memory when exact names matter: plugin tools, MCP tools, disabled-by-default tools, hints, and optional availability are environment-specific.

## Tool allowlists

A gptme run normally loads the default available toolchain. Restrict it with `--tools` or the `TOOL_ALLOWLIST` environment setting.

Common forms:

```bash
# Exact replacement: only these tools are loaded.
gptme --tools read,patch,ipython "inspect and edit this package"

# Additive: start from defaults and add more.
gptme --tools +browser,rag "research this API"

# Subtractive: start from defaults and remove high-risk tools.
gptme --tools -shell,computer "summarize this workspace"

# Empty string: no tools; pure conversation.
gptme --tools "" "explain this design"
```

Allowlist entries can be:

- exact tool names such as `read` or `shell`,
- glob patterns matched against tool names, such as `discord.*`,
- Python file paths ending in `.py` that contain top-level `ToolSpec` instances,
- hint patterns such as `hint:read-only` when tools expose capability hints.

Practical patterns:

| Goal | Suggested allowlist | Notes |
| --- | --- | --- |
| Read-only repository review | `read,chats,hint:read-only` | Built-in hint coverage may vary by release; inspect with the inventory script. |
| Minimal file-editing agent | `read,patch,patch_many` | Avoid `shell` unless tests or formatting are required. |
| Coding with execution | `read,patch,ipython,shell` | Use in trusted checkouts; shell and Python can mutate host state. |
| Web research | `browser,chats,rag` | Browser may require optional setup. |
| Safe MCP import | `+hint:read-only` or explicit `<server>.*` globs | MCP tool annotations can populate read-only/destructive/idempotent hints. |
| Custom one-file tool development | `+./my_tool.py` | `+` keeps defaults; without it the allowlist replaces defaults. |

If an allowlist names a tool that exists but is unavailable, gptme reports the tool-provided `available_hint` when available. If an allowlist excludes MCP tools unintentionally, include a glob such as `<server>.*`.

## Programmatic Tool Calling and tool formats

gptme's primary interface is Programmatic Tool Calling (PTC): the model emits executable content and gptme dispatches it to `ToolSpec.execute(code, args, kwargs)`.

### `markdown` format, default

The model writes fenced code blocks. The language tag selects the loaded tool by block type.

````markdown
```shell
printf 'hello\n'
```

```ipython
print(2 + 2)
```
````

Dispatch behavior:

1. `ToolUse.iter_from_content` scans assistant content for supported fenced code blocks.
2. The language tag maps to a loaded tool's `block_types`.
3. The block body becomes `code`; extra language-tag words become `args` except for file-writing tools that interpret the full tag.
4. `ToolUse.execute` calls the tool's `execute` function and emits `Message` results.

This path does not send JSON schemas to the model and does not parse JSON to select a tool. It is usually the most robust choice for long autonomous sessions.

### `xml` format

The XML format wraps the same executable payload in XML-like tool tags. Dispatch still ends at `ToolSpec.execute`; the content is not routed by JSON schema. Use it when a model or profile performs better with XML-structured responses.

### `tool` format

The provider-native `tool` format is for OpenAI/Anthropic-style structured tool APIs. gptme converts `ToolSpec.parameters` to provider JSON schemas, receives structured calls, parses their arguments, and then still dispatches through `ToolSpec.execute`.

Trade-offs:

| Format | Strength | Cost/risk |
| --- | --- | --- |
| `markdown` | Short, compositional, stable in long sessions, works with code-like tool use. | The model must format code fences correctly. |
| `xml` | More explicit sections for models that prefer XML. | More verbose than markdown; escaping matters. |
| `tool` | Compatible with provider-native tool routing. | Repeats schemas/history, can bloat context, and depends on accurate `parameters`. Treat JSON argument parsing as a trust boundary. |

## Dispatch and discovery architecture

Runtime discovery is layered:

1. `TOOL_MODULES` defaults to `gptme.tools` and may include additional modules.
2. Folder plugins configured under `[plugins]` contribute tool modules.
3. Entry-point plugins from the `gptme.plugins` group can contribute direct tools or tool modules.
4. MCP configuration can add external tools, named as `<server>.<tool>`.
5. `get_available_tools()` discovers `ToolSpec` instances and caches the result for the current context.
6. `init_tools(allowlist=...)` filters, initializes tools, and registers tool-provided hooks and commands.

Important implementation consequences:

- Tool state is context-local. Server workers, threads, and subagents need their own initialization.
- `ToolSpec.available` can be a boolean or callable. Inventory can mark a discovered tool unavailable without executing it.
- `disabled_by_default=True` tools are not loaded unless explicitly allowed or loaded by a context that requires them.
- `ToolSpec.functions` expose Python helper functions to the IPython-oriented prompt; `ToolSpec.execute` makes a block directly runnable.
- `ToolSpec.as_function_subtoolspecs()` can expand functions into independent `<tool>.<function>` subtools for direct invocation patterns.

## Subagent isolation summary

The `subagent` tool delegates work to child agents. Use it deliberately because it changes workspace, context, and tool inheritance.

Key controls:

| Control | Effect | Use when |
| --- | --- | --- |
| `profile="explorer"`, `"researcher"`, `"developer"`, `"verifier"` | Applies a built-in tool profile. | You want read-only research or verification without broad write access. |
| `isolated=True` | Runs the child in a temporary git worktree. | The child may edit files and you need parent workspace protection. |
| `use_subprocess=True` | Starts a fresh gptme process in the child workdir. | You want the child to load that directory's `gptme.toml` rather than inherit parent workspace context. |
| `context_mode="selective"` and `context_include=[...]` | Share only selected context components in thread mode. | You want to avoid leaking broad context to a child. |
| `context_turns=N` or `context_window=N` | Include bounded parent conversation context. | You want a child to see recent discussion without full history. |
| `redact_secrets=True` | Scrubs common secret patterns from inherited context in thread mode. | Keep the default unless a task proves it needs exact secret text. |
| `max_time` / `timeout` | Bounds child runtime or subprocess monitoring. | Any background or fan-out delegation. |

Subagents start fresh conversations by default. Completion is delivered through signal tools and parent loop notifications. Use status/read-log helpers to inspect child results rather than assuming the parent conversation contains the full child transcript.

Parallel helpers:

- `subagent_parallel(tasks, ...)`: fan out and wait for all results.
- `subagent_batch(tasks, ...)`: launch non-blocking work and collect later.
- `subagent_pipeline(items, *stages, ...)`: staged fan-out without a full barrier between stages.
- `subagent_wait_any(agent_ids, ...)`: hedge or race attempts, then cancel losers.

For concurrent file-editing children, combine explicit restricted profiles with `isolated=True`.
