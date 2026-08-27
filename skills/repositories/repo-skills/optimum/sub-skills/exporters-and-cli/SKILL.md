---
name: exporters-and-cli
description: "Use and debug Optimum's base CLI, exporter task mappings, backend
  registration, and accelerated pipeline dispatcher while respecting
  partner-package boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Optimum exporters and CLI

Use this sub-skill when the task involves:

- `optimum-cli --help`, `optimum-cli env`, `optimum-cli export`, or missing exporter subcommands such as `optimum-cli export onnx`.
- Dynamic CLI command registration through `optimum.commands.register` or `optimum.commands.optimum_cli.optimum_cli_subcommand`.
- `optimum.exporters.tasks.TasksManager` task synonyms, task/library/model mappings, backend config registration, and exporter config constructor lookup.
- `optimum.exporters.base.ExporterConfig` responsibilities for inputs, outputs, dummy inputs, dtype fields, and version gates.
- `optimum.pipelines.pipeline` accelerator selection for ONNX Runtime (`ort`) and OpenVINO (`ov`) without assuming those partner packages are installed.

Route elsewhere:

- Torch FX graph transformations and tensor parallelism -> sibling `fx-graph-workflows`.
- GPTQ / GPT-QModel quantization -> sibling `gptq-quantization`.
- Dummy input generators, normalized configs, preprocessing utilities, and config serialization details beyond exporter use -> sibling `utilities-and-configs`.

## Quick operating path

1. For CLI availability or missing subcommands, read [references/cli-reference.md](references/cli-reference.md), then run the bundled probe before writing custom inline checks:

   ```bash
   python scripts/probe_optimum_cli.py
   ```

   Add `--run-env` when the user wants the same environment report as `optimum-cli env`.

2. For task names, synonyms, backend config lookup, or custom backend registration, read [references/tasks-manager-api.md](references/tasks-manager-api.md), then run the bundled probe before inventing an ad-hoc script:

   ```bash
   python scripts/tasks_manager_probe.py
   ```

   Use `--backend`, `--model-type`, and `--task` to probe a specific mapping without downloading models.

3. For accelerated inference via `optimum.pipelines.pipeline`, read [references/pipelines-and-partner-packages.md](references/pipelines-and-partner-packages.md). Treat ONNX Runtime and OpenVINO as optional partner implementations; the base package only dispatches to them.

4. For failure diagnosis, start with [references/troubleshooting.md](references/troubleshooting.md).

## Non-negotiable boundaries

- Do not tell users that base `optimum` alone implements ONNX export, ONNX Runtime optimization/quantization, or OpenVINO inference. Those commands and model classes are provided by partner packages such as `optimum-onnx` and `optimum-intel`.
- Do not run export, pipeline inference, model loading from the Hub, or native source tests unless the user explicitly allows the needed partner packages, network/cache, and runtime budget.
- Use the bundled scripts as safe probes only: they inspect installed package state, command help, and in-memory API behavior; they do not write package files, download models, train, export, quantize, or require credentials.

## Bundled references and scripts

- [CLI reference](references/cli-reference.md)
- [TasksManager and ExporterConfig API](references/tasks-manager-api.md)
- [Pipelines and partner packages](references/pipelines-and-partner-packages.md)
- [Troubleshooting guide](references/troubleshooting.md)
- [CLI probe script](scripts/probe_optimum_cli.py)
- [TasksManager probe script](scripts/tasks_manager_probe.py)
