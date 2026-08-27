# SDK And Tools Troubleshooting

## Common Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| A shared package will not import | The package or one of its optional dependencies is missing from the environment | Install the smallest package set that includes the workflow's extras |
| `ToolRegistry` refuses to start | `TOOL_REGISTRY_CONFIG_PATH` or storage credentials are missing | Point it at a config directory and provide the storage credential envs |
| A registry load tries to do too much | `load_tools_to_json.py` is operational and may pull images / write JSON | Use a validation helper when you only need a dry inspection |
| A tool container cannot talk to the platform | `PLATFORM_SERVICE_*` or `EXECUTION_DATA_DIR` is missing / wrong | Check the example tool's required runtime variables |
| Text extraction fails but the tool container looks fine | The x2text service or its API key / port contract is missing | Check the x2text service env vars and the platform API key |
| Tool metadata looks wrong in the platform | `properties.json`, `spec.json`, and runtime variables drifted apart | Compare the metadata files in the tool config directory |

## Dependency / Backend Notes

- `unstract-sdk1` has optional cloud-provider extras; do not install them unless the workflow actually uses those providers.
- `unstract-connectors` contains many provider-specific dependencies. Live connector tests are not the same thing as the base package import check.
- `unstract-filesystem` and `unstract-workflow-execution` depend on the shared package family, so a failure there may be a missing shared dependency rather than a bug in the leaf package.

## Tool-Container Notes

- The tool protocol is stdin / stdout based. A tool that reads files implicitly or writes ad hoc log lines outside the protocol is misbehaving.
- `EXECUTION_DATA_DIR` must be treated as a per-run working directory for the tool.
- Example tools expect the platform / x2text / execution-data contracts to be satisfied before they can run.

## What To Check First

1. Confirm the exact package or tool surface the user asked about.
2. Confirm the shared package and optional-extras set that surface needs.
3. Confirm the registry directory or runtime-variable schema if the task is tool-oriented.
4. Confirm the platform / x2text / execution-data dependencies if the task is one of the example tools.
