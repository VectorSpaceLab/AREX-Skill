---
name: generation-runtime
description: "Run DataDesigner through the Python API for validate,
  check_models, preview, create, workflow chaining, resume, export, and runtime
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Generation Runtime

Use this sub-skill when you need to execute DataDesigner from Python rather than author column configs or map CLI commands.

## Start here

- [API Reference](references/api-reference.md) — public `DataDesigner`, `DatasetCreationResults`, `PreviewResults`, `RunConfig`, and workflow signatures.
- [Runtime Workflows](references/runtime-workflows.md) — recommended validate → readiness → preview → create flow, async usage, and workflow chaining.
- [Artifacts, Results, and Resume](references/artifacts-results-and-resume.md) — artifact tree, result semantics, resume modes, and export / push-to-hub behavior.
- [Troubleshooting](references/troubleshooting.md) — model and MCP readiness failures, early shutdown, resume incompatibility, export issues, and TTY logging differences.
- [Sampler Smoke Script](scripts/smoke_sampler_generation.py) — deterministic local smoke that avoids remote APIs.

## Use this sub-skill for

- Running `DataDesigner.validate`, `preview`, `create`, `acreate`, `check_models`, `set_run_config`, and `compose_workflow`.
- Inspecting `PreviewResults` and `DatasetCreationResults` outputs, artifact paths, processor outputs, export files, and resume checkpoints.
- Diagnosing model alias, MCP tool alias, or async/runtime issues during local generation.
- Understanding when `validate` still works even when no usable model aliases exist.

## Route away

- [config-authoring](../config-authoring/SKILL.md) — column definitions, sampler settings, constraints, processors, and config-building guidance.
- [cli-and-agent-tools](../cli-and-agent-tools/SKILL.md) — CLI command parsing, state files, and command-to-API mapping.
- [plugins-and-extensions](../plugins-and-extensions/SKILL.md) — plugin packaging, install, and discovery.
- [recipes-and-integrations](../recipes-and-integrations/SKILL.md) — recipe-specific, long-form usage patterns that build on the runtime API.

## Safety defaults

- Prefer sampler-only smoke runs first when model aliases are missing or untrusted.
- Use `validate` before `check_models`; `validate` only checks the configuration shape and can succeed without usable model aliases.
- Set `RunConfig(display_tui=False, otel_metrics_port=None)` when you want quiet local generation and no terminal UI.
- Keep `buffer_size`, `preserve_dropped_columns`, and the workflow stage layout unchanged when resuming a run.
- Do not call `push_to_hub` from the smoke helper; it requires network access and a valid Hugging Face token.
