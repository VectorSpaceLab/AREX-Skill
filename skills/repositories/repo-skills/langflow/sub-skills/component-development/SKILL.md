---
name: component-development
description: "Create and maintain Langflow Python components, extension bundles,
  component indexes, and component tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Langflow Component Development

Use this sub-skill when adding, updating, packaging, or testing Langflow Python components. It covers `Component` subclasses, inputs/outputs, extension bundles, dynamic loading, component index rebuilds, and component test structure.

## Route First

- Use this sub-skill for Python component classes, `inputs`, `outputs`, `Message`/`Data`/`DataFrame` returns, bundle manifests, extension entry points, `LFX_DEV`, component index rebuilds, and component unit tests.
- Route backend API routes, services, auth, database, and graph internals to `../backend-runtime/SKILL.md`.
- Route frontend icon import maps, React UI wiring, Vite, Jest, and Playwright work to `../frontend-development/SKILL.md`.
- Route release automation, broad monorepo formatting/linting, version bumps, and CI policy to `../repo-maintenance/SKILL.md`.

## Core Workflow

1. Preserve identity before changing code: do not rename a released component class or its `name` attribute unless you intentionally create a new component and keep the old one as `legacy = True`.
2. Define or update the `Component` subclass with stable metadata, serializable inputs, and `Output(..., method="...")` entries that point to real instance methods.
3. Return Langflow schema objects (`Message`, `Data`, `DataFrame`) or integration objects expected by downstream handles; avoid returning raw provider responses unless the output contract says so.
4. For built-in components, place the class in the correct component category and update category exports or dynamic import maps consistently with the existing package pattern.
5. For extension bundles, package components behind a valid `extension.json` or `[tool.langflow.extension]` manifest and a `langflow.extensions` entry point.
6. Validate with the bundled skeleton helper first, then use focused native checks such as component unit tests, extension validation, and component index rebuilds when safe.

## References

- `references/component-api.md` explains component class shape, metadata, inputs, outputs, return values, async behavior, and compatibility rules.
- `references/bundles-and-indexes.md` explains extension manifests, pyproject entry points, bundle IDs, dynamic loading, and component index rebuilds.
- `references/troubleshooting.md` maps common import, schema, CLI/API, runtime, credential, network, and hardware failures to fixes.

## Helper Script

Run the local skeleton checker from this skill tree before deeper tests:

```bash
python scripts/check_component_skeleton.py path/to/component.py
python scripts/check_component_skeleton.py path/to/component.py --class MyComponent --import-module
```

The default mode parses Python only and is safe for components with missing optional dependencies. `--import-module` performs runtime checks and can import provider SDKs, so use it only in an environment with the component's dependencies installed.

## Focused Validation Commands

Use the smallest safe command that covers the change:

```bash
python -m py_compile path/to/component.py
python scripts/check_component_skeleton.py path/to/component.py
make build_component_index
lfx extension validate path/to/extension/root
python -m pytest src/backend/tests/unit/components/<category>/test_<component>.py -q
```

For components requiring API keys, databases, GPUs, local OCR, Torch, or network services, keep the static checks runnable and mark native tests with the appropriate skip/credential guard instead of forcing credentials into tests.

## Evidence Distilled

This guidance is distilled from Langflow component contribution docs, component test docs, extension manifest docs, the `lfx` `Component` implementation, the `langflow` compatibility shim, IO exports, bundle `pyproject.toml`/manifest patterns, the component index builder, and existing component tests. Runtime files here are self-contained; source paths are evidence names, not required reading for future agents.
