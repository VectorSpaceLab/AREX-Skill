# Built-in Tools Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| A tool name cannot be resolved | The module was not imported or registration is missing. | Import the tool definition module or call the preset registration helper. |
| `browser_tool_set` is unavailable | Chromium/browser runtime cannot be found. | Check `BrowserToolSet.is_usable()` and install a browser only when that workflow is needed. |
| Workflow script rejected | Missing `async def main(wf)` or unsafe access. | Follow the workflow tool contract and keep file/shell operations in sub-agents. |
| A custom tool disappears in a remote server | The server did not preload the module or its path. | Use the remote-runtime helper for `--import-modules` and `OH_EXTRA_PYTHON_PATH`. |
