# Package And Tooling Overview

This repo ships a small family of shared Python packages plus a containerized tool protocol used by the platform and example tools.

## Shared Package Map

| Package | What it provides | Notable dependencies / extras |
| --- | --- | --- |
| `unstract-sdk1` | SDK surface for tool authors: LLM helpers, file storage, prompt / adapter helpers, and utility APIs | Optional `aws`, `gcs`, `azure` extras |
| `unstract-core` | Shared core helpers used across services | Optional `flask` extra |
| `unstract-filesystem` | Storage abstraction used by workflow execution | Depends on `unstract-sdk1` |
| `unstract-flags` | gRPC-based feature-flag helpers | gRPC / protobuf dependencies |
| `unstract-tool-registry` | Registry-backed tool metadata loading | Depends on `unstract-sdk1`, `unstract-tool-sandbox`, `unstract-flags` |
| `unstract-tool-sandbox` | Tool-container inspection and protocol helpers | Paired with registry loading |
| `unstract-workflow-execution` | Workflow execution service objects and DTOs | Depends on the other shared packages |
| `unstract-connectors` | Filesystem and database connector implementations | Optional provider-specific dependencies |

## Tool Protocol

The `tools/` directory describes the contract that every containerized tool follows.

### Inputs And Outputs

- Tools read input from stdin and/or command-line arguments.
- Tools write newline-delimited JSON to stdout.
- Tool definitions live in `config/properties.json`.
- Tool settings live in `config/spec.json`.
- Runtime-variable schemas live in `config/runtime_variables.json`.
- Tool icons live in `config/icon.svg`.

### Message Types

The protocol supports messages such as `SPEC`, `PROPERTIES`, `ICON`, `VARIABLES`, `LOG`, `COST`, `RESULT`, and `SINGLE_STEP_MESSAGE`.

### Tool Metadata Fields

Important `properties.json` fields include:

- `display_name`
- `function_name`
- `description`
- `parameters`
- `versions`
- `input_type` / `output_type`
- `requires.files.*` / `requires.databases.*`

## Example Tools

### Classifier

- Requires platform-service connectivity and an execution data directory.
- Uses runtime variables such as `PLATFORM_SERVICE_HOST`, `PLATFORM_SERVICE_PORT`, `PLATFORM_SERVICE_API_KEY`, and `EXECUTION_DATA_DIR`.
- Supports `SPEC`, `PROPERTIES`, `ICON`, `VARIABLES`, and `RUN` commands.

### Text Extractor

- Uses the x2text service plus platform-service connectivity.
- Requires `PLATFORM_SERVICE_HOST`, `PLATFORM_SERVICE_PORT`, `PLATFORM_SERVICE_API_KEY`, `EXECUTION_DATA_DIR`, `X2TEXT_HOST`, and `X2TEXT_PORT`.
- The tool writes updated input metadata back into its execution data directory, so the directory must be reset between runs.

## Tool Registry Flow

- `TOOL_REGISTRY_CONFIG_PATH` points at a config directory.
- `registry.yaml` lists the tool images.
- `private_tools.json` and `public_tools.json` hold the materialized tool metadata.
- `load_tools_to_json.py` is the operational loader that reads the registry and writes the JSON outputs.
- Use the bundled checker from the root skill tree to validate a registry directory without pulling images.

## How To Read This File

Use this file when you need to understand how the shared packages, example tools, and registry fit together before writing or debugging a tool / SDK workflow.
