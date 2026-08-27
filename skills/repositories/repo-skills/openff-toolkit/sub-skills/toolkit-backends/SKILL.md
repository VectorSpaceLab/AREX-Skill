---
name: toolkit-backends
description: "Choose, inspect, and troubleshoot OpenFF Toolkit optional backend
  wrappers and ToolkitRegistry behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Toolkit Backends

Use this sub-skill when a task involves OpenFF Toolkit optional cheminformatics backends, wrapper availability, `ToolkitRegistry` precedence, `GLOBAL_TOOLKIT_REGISTRY`, `toolkit_registry_manager`, supported file formats, supported charge methods, or dependency/license failures for RDKit, OpenEye, AmberTools, OpenFF NAGL, or the built-in wrapper.

## Start Here

1. Run `python scripts/check_toolkit_backends.py --json` when you need environment-specific backend facts.
2. Read `references/backend-reference.md` to choose wrappers, registries, optional installs, and supported file/charge capabilities.
3. Read `references/troubleshooting.md` when a wrapper is unavailable, a method cannot be resolved, a file format or charge method is unsupported, or OpenEye/RDKit behavior differs.

## Routing Boundaries

- Handle backend readiness first: availability, registry construction, wrapper ordering, explicit `toolkit_registry=` use, and optional dependency guidance.
- Route molecule construction, file conversion, topology loading, force-field parameterization, and chemistry workflows back to the relevant OpenFF Toolkit domain sub-skill after backend selection is settled.
- Do not rely on global registry mutation unless the user specifically needs process-wide behavior; prefer explicit wrapper/registry arguments or `toolkit_registry_manager` for temporary changes.
