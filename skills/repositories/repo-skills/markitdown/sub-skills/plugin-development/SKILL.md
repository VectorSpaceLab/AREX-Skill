---
name: plugin-development
description: "Build, inspect, and troubleshoot MarkItDown third-party plugins
  and custom DocumentConverter registration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MarkItDown Plugin Development

Use this sub-skill when a task involves authoring, packaging, discovering, enabling, or debugging third-party MarkItDown plugins. Plugins add custom `DocumentConverter` classes through installed Python package entry points and are disabled unless explicitly enabled.

## Start Here

- For plugin package shape, entry points, converter APIs, registration, priorities, and plugin-enabled conversion, read [references/authoring-reference.md](references/authoring-reference.md).
- For the distilled sample RTF plugin pattern, read [references/sample-plugin-walkthrough.md](references/sample-plugin-walkthrough.md).
- For missing plugins, warning-only plugin failures, stream-position assertions, priority surprises, and disabled plugins, read [references/troubleshooting.md](references/troubleshooting.md).
- To inspect an installed plugin package without the original plugin source tree, run `python scripts/check_plugin_package.py --plugin <entry-point-name>` from this sub-skill directory.

## Routing Boundaries

- Use this sub-skill for `DocumentConverter.accepts`, `DocumentConverter.convert`, `DocumentConverterResult`, `StreamInfo`, `register_converters`, `__plugin_interface_version__`, `MarkItDown.register_converter`, package entry points in the `markitdown.plugin` group, `enable_plugins=True`, `markitdown --list-plugins`, and `markitdown --use-plugins`.
- Route OCR-specific plugin setup and behavior to `../ocr-plugin/SKILL.md`; treat it as a real plugin example, not as the generic authoring guide.
- Route built-in converter usage, core conversion APIs, and non-plugin conversion errors to `../core-conversion/SKILL.md`.
- Route MCP server plugin environment variables and serving behavior to `../mcp-server/SKILL.md`.
- Exclude PyPI release automation and plugin systems that are not MarkItDown entry-point plugins.

## Quick Checklist

1. Package the plugin module with a `[project.entry-points."markitdown.plugin"]` entry whose key is the plugin name and whose value is the importable module.
2. Export `__plugin_interface_version__ = 1` and `register_converters(markitdown: MarkItDown, **kwargs)` from that module.
3. Implement each converter as a `DocumentConverter` with `accepts(file_stream, stream_info, **kwargs)` and `convert(file_stream, stream_info, **kwargs)`.
4. Register converters with `markitdown.register_converter(converter, priority=<float>)`; lower priority values are tried first and equal priorities retain stable order.
5. Verify discovery with `markitdown --list-plugins`, then verify runtime conversion with `markitdown --use-plugins <file>` or `MarkItDown(enable_plugins=True)`.
