# Tools and extensibility troubleshooting

Use this guide after reading the relevant operating reference:

- [tools-reference.md](tools-reference.md) for built-in tools and allowlists;
- [extensibility.md](extensibility.md) for custom tools, plugins, hooks, skills, and lessons;
- [mcp-browser-computer.md](mcp-browser-computer.md) for MCP, browser, and desktop automation.

## First checks

Run safe static checks before executing any tool/plugin/MCP/browser/desktop workflow:

```bash
python scripts/list_gptme_tools.py --format text --check-browser
python scripts/validate_plugin_skeleton.py PATH_TO_PLUGIN
```

Then classify the failure:

| Symptom | Likely layer | Next step |
| --- | --- | --- |
| Tool name not found | allowlist/discovery | Check exact name, `--tools` replacement vs `+`, plugin/MCP discovery. |
| Tool found but unavailable | optional dependency/service | Read `available_hint`, install optional extra/system command, or route to a safer substitute. |
| Tool present but not loaded | allowlist/disabled default | Explicitly include it in `--tools` or load context-specific signal tools. |
| Tool block ignored | tool format/block type | Check language tag maps to a loaded `block_types` value. |
| Provider-native tool call fails | `tool` format parameter schema | Check `ToolSpec.parameters` and string-to-type coercion inside `execute`/function code. |
| Plugin not discovered | config/path/package shape | Validate `__init__.py`, importable name, component dirs, enabled allowlist. |
| Hook runs with wrong args | stale signature | Use current `HookType` values and data-object signatures for tool execution hooks. |
| MCP tools absent | config/allowlist/transport | Check `[mcp] enabled`, server enabled, `gptme-util mcp list/test`, and `<server>.*` allowlist. |
| Browser fails | backend/browser binary/CDP/site | Separate Python package, browser binary, env vars, and site blocking. |
| Computer tool fails | display/system permissions | Check X11/macOS dependencies, display target, and permissions. |

## Tool allowlist and denied-tool issues

Common mistakes:

- `--tools ./my_tool.py` replaces the default toolset with only the file tool. Use `--tools +./my_tool.py` to add it to defaults.
- `--tools read,patch` omits `shell` and `ipython`, so test commands and Python snippets will be denied or ignored.
- A glob such as `server.*` is needed for grouped MCP tools if exact MCP tool names are not known.
- Disabled-by-default signal tools (`complete`, `clarify`, `progress`, some interaction tools) may only load in specific autonomous/subagent contexts or when explicitly allowed.
- `hint:read-only` depends on tool hints. Built-in and MCP hint coverage can vary; inspect with the inventory script.

Repair pattern:

1. Run `python scripts/list_gptme_tools.py --format text`.
2. Check whether the desired tool is `available`, `disabled_by_default`, and has the expected `block_types`.
3. Rebuild the allowlist with exact names first; add globs/hints only after confirming they match.
4. For risky tools, prefer a narrower allowlist rather than broad defaults.

## Custom tool failures

| Symptom | Cause | Repair |
| --- | --- | --- |
| File tool not discovered | No top-level `ToolSpec` instance. | Define a module-level variable assigned to `ToolSpec(...)`. |
| Tool discovered but code block ignored | Missing `block_types`. | Add `block_types=["yourtag"]` and use that tag in fenced blocks. |
| Provider-native `tool` mode call has empty/malformed args | Missing or weak `parameters`. | Add `Parameter` entries; coerce string `kwargs` to needed types in the function. |
| Import fails at startup | Tool module imports optional dependency eagerly. | Move optional imports into `available` checks or `execute`, and add `available_hint`. |
| Tool works with `ipython` functions but not as a direct block | `functions` provided but no `execute`. | Add `execute` or use `ToolSpec.from_function`/function subtools where appropriate. |
| Tool mutates unexpectedly | No confirmation/allowlist guard. | Mark hints/destructiveness, document side effects, and keep dangerous behavior explicit. |

Use quick development loading only for trusted local files:

```bash
gptme --tools +./my_tool.py "try my custom tool"
```

## Plugin discovery failures

Folder plugin checklist:

- Plugin directory contains `__init__.py`.
- Directory name is a valid Python identifier for folder plugins. If the distribution name contains a hyphen, use an installable package with a valid import package under `src/` or an entry-point plugin.
- At least one component directory exists: `tools/`, `hooks/`, or `commands/`.
- `tools/` has public `.py` files with `ToolSpec` instances. A `tools/` package with only `__init__.py` can appear empty to folder-plugin discovery.
- Hook and command modules define `register()` and call `register_hook()` or `register_command()` inside it.
- The plugin path is included under `[plugins].paths` and the name is included in `[plugins].enabled` if that allowlist is present.
- Required dependencies are installed in the same Python environment as gptme.

Entry-point plugin checklist:

- `pyproject.toml` declares `[project.entry-points."gptme.plugins"]`.
- The entry point resolves to a `GptmePlugin` instance or a factory returning one.
- The package was reinstalled after changing entry points.
- Folder plugin with the same name is not shadowing the entry point.

Run:

```bash
python scripts/validate_plugin_skeleton.py PATH_TO_PLUGIN
```

The validator is static; it catches shape mistakes without importing plugin code. Passing it does not prove runtime dependencies are installed.

## Hook registration and signature failures

Common stale patterns:

- Old names like `TOOL_PRE_EXECUTE` or `TOOL_POST_EXECUTE`; current names are `TOOL_EXECUTE_PRE` and `TOOL_EXECUTE_POST`.
- Tool execution hooks expecting positional `(log, workspace, tool_use)`. Current pre/post execution hooks receive `ToolExecutePreData` or `ToolExecutePostData`.
- Hook function returns a list instead of yielding `Message` objects or returning `None`.
- Hook does network/browser/model work synchronously and slows every turn/tool call.
- Hook registration happens at import time in a module that is not discovered or not loaded.

Repair pattern:

```python
from gptme.hooks import HookType, register_hook


def on_tool_post(data):
    # data.log, data.workspace, data.tool_use, data.result_msgs
    yield


def register():
    register_hook("my_plugin.tool_post", HookType.TOOL_EXECUTE_POST, on_tool_post, priority=0)
```

Keep hook errors non-fatal: catch predictable exceptions and yield hidden diagnostic messages only when useful.

## MCP server failures

| Symptom | Likely cause | Repair |
| --- | --- | --- |
| `gptme-util mcp list` says MCP disabled | `[mcp].enabled` false or missing. | Enable MCP in config for the environment where gptme runs. |
| Server not found | Name mismatch or config not loaded. | Check `name`, config path, and workspace/user config precedence. |
| Stdio server fails immediately | `command` missing, wrong args, dependency not installed. | Run the command manually with `--help`; pin package managers and args. |
| HTTP server fails | URL/header/auth/network problem. | Probe endpoint outside gptme; avoid logging secret header values. |
| MCP tools are discovered but not usable | Tool allowlist excludes `<server>.<tool>`. | Add exact names or `<server>.*`. |
| gptme MCP server protocol breaks | Logs printed to stdout or client config wrong. | Keep logs on stderr; use `gptme-mcp-server --help` and minimal tool set. |

For gptme as an MCP server, start with read-only or file-only exposure. Exposing `shell` and `ipython` grants code execution to the MCP client.

## Browser failures

Difficult case: browser task fails because Playwright is installed but the actual browser binary is missing, or CDP is configured incorrectly.

Diagnosis sequence:

1. Run `python scripts/list_gptme_tools.py --check-browser`.
2. If Playwright is absent and Lynx is absent, install a browser backend or route to a non-browser workflow.
3. If Playwright is present but the browser launch fails, install the matching Playwright browser binary for the installed Playwright version.
4. If `GPTME_BROWSER_CDP_URL` is set, confirm a Chromium-compatible browser was started with remote debugging and the URL is reachable. CDP mode ignores `GPTME_BROWSER_ENGINE`.
5. If a site blocks headless Chromium, try `GPTME_BROWSER_ENGINE=firefox`.
6. If a site requires a visible logged-in browser session, use CDP with an already-open Chromium browser or, with explicit authorization, the computer tool in a desktop environment.
7. If the failure is CAPTCHA, payment, account security, or bot detection, do not attempt bypass; ask the user for an approved path.

Keep provider-native search and model/provider credentials routed to configuration-and-providers.

## Computer-use failures

| Symptom | Likely cause | Repair |
| --- | --- | --- |
| No screenshot | No display, missing screenshot backend, or permissions. | Check `DISPLAY` on Linux or screen-recording permission on macOS. |
| Click/key actions fail on Linux | Missing `xdotool` or wrong X11 display. | Install `xdotool`, confirm target display and visible window. |
| Accessibility tree empty on Linux | Missing AT-SPI2/`pyatspi` or inaccessible desktop. | Install system accessibility package and Python binding; verify desktop session. |
| macOS input fails | Missing `cliclick` or Accessibility permission. | Install `cliclick` and grant terminal accessibility permission. |
| Coordinates wrong | Resolution/scaling mismatch. | Capture screenshot, verify `WIDTH`/`HEIGHT`, and prefer accessibility element clicks. |
| Sensitive action blocked | `GPTME_COMPUTER_CONFIRM_SENSITIVE=1` in non-interactive mode. | Use interactive confirmation or redesign task to avoid sensitive action. |

Never use computer control for destructive or financial/account actions without an explicit user approval step. Prefer browser/API/shell workflows when they can solve the task safely.

## Skills and lessons failures

| Symptom | Cause | Repair |
| --- | --- | --- |
| Skill does not auto-load | gptme skills trigger by skill name, not keywords. | Mention the skill name or explicitly read the `SKILL.md`. |
| Lesson does not auto-load | Missing/invalid `match` frontmatter or keyword mismatch. | Add `match.keywords`/`match.tools` and test with lesson search. |
| Skill helper script not executed automatically | Skills do not auto-run scripts or install dependencies. | Tell the agent/user to run helper scripts manually or use a plugin for runtime behavior. |
| Runtime hook expected from a lesson/skill | Lessons and skills are knowledge only. | Implement a plugin hook and optionally add a lesson/skill for guidance. |

Useful native help checks:

```bash
gptme-util skills --help
gptme-util skills list
gptme-util skills dirs
```

## Maintainer-only evidence candidates

If a user is maintaining a gptme checkout and dev dependencies are installed, focused tests for this sub-skill can include tool, plugin, hook, MCP, and lesson unit tests. Do not run full browser/computer integration tests, networked MCP registry tests, provider calls, or Docker workflows unless the user explicitly authorizes those heavier surfaces.
