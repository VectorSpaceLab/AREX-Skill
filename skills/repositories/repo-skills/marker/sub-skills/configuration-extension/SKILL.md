---
name: configuration-extension
description: "Configure and extend Marker pipelines with ConfigParser, class
  paths, processors, renderers, providers, and schema/debug guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Marker Configuration And Extension

Use this sub-skill when a task is about changing how Marker parses options, selects pipeline classes, injects processors/renderers/providers, or explains debug/schema output. For routine conversion commands and Python conversion calls, route to `../conversion-cli-api/`. For LLM service credentials, extraction schemas, and LLM backend behavior, route to `../llm-extraction-services/`. For Streamlit apps, FastAPI server, or deployment, route to `../server-deployment/`.

## Start Here

1. Decide whether the user needs configuration, extension design, or debugging:
   - Configuration: inspect `ConfigParser` output, `config_json`, generated common options, `--processors`, `--converter_cls`, `--output_format`, and `--debug`.
   - Extension: choose the right ownership point: provider for input format, builder for document construction, processor for block mutation, renderer for output shape, converter for end-to-end orchestration.
   - Debugging: check JSON validity, falsey values, class-path imports, renderer/output mismatches, provider detection, and debug artifact placement.
2. Use [`scripts/inspect_marker_config.py`](scripts/inspect_marker_config.py) before running conversion when a user asks what CLI/config options pass downstream.
3. Use [`scripts/custom_processor_template.py`](scripts/custom_processor_template.py) as a safe skeleton or import validator for custom processor class paths.
4. Keep custom class paths fully qualified, for example `marker.converters.table.TableConverter`, not `TableConverter`.

## Key References

- [`references/configuration.md`](references/configuration.md): `ConfigParser`, `config_json`, generated options, class-path helpers, and safe inspection workflow.
- [`references/extension-points.md`](references/extension-points.md): pipeline anatomy, default processors, provider/builder/processor/renderer ownership, and extension planning.
- [`references/debugging-and-schema.md`](references/debugging-and-schema.md): debug artifact behavior, renderer output contracts, JSON/chunks schema, and schema/block notes.
- [`references/troubleshooting.md`](references/troubleshooting.md): common config, import, renderer, provider, debug, dependency, and schema failures.

## Fast Routing

- User asks “How do I convert this folder/PDF?” → `../conversion-cli-api/`.
- User asks “How do I use Gemini/OpenAI/Claude/Ollama or structured extraction?” → `../llm-extraction-services/`.
- User asks “How do I run the API server or GUI?” → `../server-deployment/`.
- User asks “What does this config pass into Marker?” → inspect with [`scripts/inspect_marker_config.py`](scripts/inspect_marker_config.py), then apply [`references/configuration.md`](references/configuration.md).
- User asks “Where should I add a custom behavior?” → use the ownership map in [`references/extension-points.md`](references/extension-points.md).

## Safe Defaults

- Prefer dry-run inspection before conversion. Config inspection does not open input documents or call model services.
- Keep credential setup out of examples unless the LLM sub-skill explicitly owns the task.
- Avoid editing Marker internals for user projects when a full import path, config key, custom processor, or custom renderer can be passed into existing APIs.
- Explain that `--debug` writes extra artifacts under the configured output directory, nested by document base name.
