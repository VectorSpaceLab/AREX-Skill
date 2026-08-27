# Troubleshooting

Cross-cutting problems that recur across Upsonic workflows belong here. Route workflow-specific issues to the owning sub-skill's troubleshooting file.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'upsonic'` | The package is not installed into the active interpreter. | Reinstall with `python -m pip install -e .` from the repo checkout or `python -m pip install upsonic` for a published release. |
| `upsonic --help` works but a command fails immediately | The wrong working directory or a missing config file is usually the cause. | Re-run from the project directory and read the CLI route that owns the command. |
| `upsonic run` says `upsonic_configs.json` is missing | The project was not initialized or the config was moved. | Run `upsonic init` or restore the config next to `main.py`. |
| Model/provider errors mention an unknown provider or model | The `provider/model` string is malformed, deprecated, or the provider SDK is missing. | Re-check the model string, confirm the provider prefix, and install the matching provider extra. |
| A tool or MCP call is rejected | `ToolConfig` flags can be mutually exclusive and MCP commands are sanitized. | Simplify the tool config, remove conflicting HITL flags, and check `upsonic[mcp]` / command safety. |
| Chat or memory calls fail after a backend swap | The selected storage backend or its connection string is unavailable. | Use a working backend first, then add the desired storage extra and credentials. |
| RAG ingestion fails on documents or OCR | The required loaders / vector DB / OCR extras are missing. | Install the matching `loaders`, `vectordb`, `embeddings`, or `ocr` extra and retry with a tiny fixture. |
| Agent or autonomous workflows complain about blocked shell commands | The sandbox or safety guard intentionally blocked the command. | Rewrite the command to stay inside the workspace and remove dangerous shell patterns. |

## Shared recovery order

1. Import-check the base package.
2. Read the route-specific references for the workflow.
3. Check the optional extra or backend declared by the route.
4. Use the bundled helper script for a safe smoke test.
5. Only then run a native example or test.
