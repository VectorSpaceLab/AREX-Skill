---
name: api-extension
description: "Guides Nerfstudio custom method and dataparser packaging,
  entry-point registration, config objects, and plugin discovery checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# API Extension

Use this route when the task is to add or debug a custom Nerfstudio method or dataparser package, rather than using only the built-in models.

## What this route covers

- `MethodSpecification` and `DataParserSpecification` registration patterns.
- Pyproject entry points for `nerfstudio.method_configs` and `nerfstudio.dataparser_configs`.
- Temporary registration through `NERFSTUDIO_METHOD_CONFIGS` and `NERFSTUDIO_DATAPARSER_CONFIGS`.
- Discovery behavior visible in `ns-train --help` and the plugin registry tests.
- Boundaries between public extension packages and built-in Nerfstudio method/dataparser routes.

## What this route excludes

- Training built-in methods: use `training-and-configs`.
- Data conversion or `transforms.json` validation: use `data-preparation`.
- Viewer, rendering, or export work: use `visualization-and-export`.

## Read these bundled files

- [`references/extension-guide.md`](references/extension-guide.md) for packaging and registration patterns.
- [`references/api-reference.md`](references/api-reference.md) for the verified plugin classes and behavior.
- [`references/troubleshooting.md`](references/troubleshooting.md) for registration and discovery failures.

## Typical workflow

1. Define a typed dataclass or specification wrapper for the new method/dataparser.
2. Register it as a package entry point or with the temporary environment variable during development.
3. Reinstall the package in editable mode so discovery can see the new entry point.
4. Confirm the new method/dataparser appears in the right CLI help or registry result.
