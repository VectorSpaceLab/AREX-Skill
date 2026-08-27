# Tool Catalog

## Default tool names

| Tool name | Main purpose | Notes |
| --- | --- | --- |
| `terminal` | Run shell commands in a persistent terminal session. | Use for command sequences and process interaction. |
| `file_editor` | View, create, and edit plain-text files. | Use absolute host-native paths. |
| `task_tracker` | View or plan a task list for conversation state. | Useful for simple task management. |
| `browser_tool_set` | Browser automation and page interaction. | Optional and environment dependent; usability depends on Chromium/browser detection. |
| `task_tool_set` | Delegate work to a sub-agent task tool. | Used when the agent needs a dedicated task runner. |
| `workflow_tool_set` / `workflow` | Execute generated Python orchestration scripts. | Scripts must define `async def main(wf)`. |
| `apply_patch` | Apply patch-style edits. | Use for patch-oriented workflows. |
| `grep` | Search text in files. | Prefer `rg`/grep-backed search helpers where possible. |
| `glob` | Expand filesystem patterns. | Use for file discovery. |
| `planning_file_editor` | Structured planning edits. | Maintainer and planning workflows. |
| `delegate` | Lightweight delegation. | Usually handled through higher-level agent features. |
| `tom_consult` | Ask a TOM-style consult tool. | Specialized internal helper. |
| `sleeptime_compute` | Internal compute helper exposed by tom consult. | Utility tool. |

## Registry behavior

- `register_tool(name, factory)` adds a tool definition or tool class.
- `list_registered_tools()` preserves registration order.
- `list_usable_tools()` filters by `is_usable()` when a tool class defines it.
- `get_tool_module_qualnames()` helps map a tool name back to its module.

## Default presets

`get_default_tools(enable_browser=False, enable_sub_agents=False)` returns the canonical default tool specs. `get_default_agent(cli_mode=True)` disables browser tools for CLI-friendly usage.
