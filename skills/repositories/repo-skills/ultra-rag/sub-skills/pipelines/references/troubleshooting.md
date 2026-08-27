# UltraRAG Pipeline Troubleshooting

## Purpose

Use this when a pipeline build or run fails after the package and server
imports succeed.

## Failure patterns

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Not found: <name>` during build | Pipeline file name is wrong or not under a discovered pipeline root | Confirm the file exists and that you are using the pipeline stem, not the full path. |
| `Cannot find the server file` | The pipeline points to a server directory whose `src/<name>.py` is missing | Fix the `servers:` entry or regenerate the server layout. |
| Generated `server.yaml` / `parameter.yaml` look stale | Server code changed after the last build | Re-run `ultrarag build <pipeline.yaml>` to refresh the generated configs. |
| `Missing value for key(s)` | A step input name does not match the upstream output or parameter keys | Check the step remapping and the server's registered output names. |
| `Unsupported server type` | The server path is neither a local `.py` file nor an HTTP MCP endpoint | Convert the server path to a local Python file or a supported remote MCP URL. |
| Node.js error during build or run | The pipeline includes an HTTP MCP server path and needs `mcp-remote` | Install Node.js 20+ and re-run the command. |
| Server subprocess says `ModuleNotFoundError: No module named 'ultrarag'` even though the parent process imports it | The client starts server processes with command `python`, so PATH points at the wrong interpreter | Prepend the intended environment's `bin/` or `Scripts/` directory to PATH before build/run, or use the bundled smoke script pattern. |
| `show case` cannot open the case data | There is no `memory_*.json` file or the file is not in the expected case format | Provide a memory export or a case JSON/JSONL file with the expected step/memory structure. |
| `ultrarag run` succeeds but the answer is empty | The final step did not produce the expected output key | Check the last prompt/generation remap and the evaluation expectations. |

## Debugging order

1. Check the pipeline YAML syntax.
2. Verify the server paths.
3. Compare step input and output names against the generated server config.
4. Rebuild the pipeline.
5. Only then inspect the backend module or UI if the problem persists.

## Useful next checks

- `references/pipeline-dsl.md` for the YAML shapes and data-flow rules.
- `scripts/smoke_sayhello_pipeline.py` for a known-good orchestration path.
- `sub-skills/servers/references/troubleshooting.md` if the error is actually a
  backend or optional-dependency failure.
