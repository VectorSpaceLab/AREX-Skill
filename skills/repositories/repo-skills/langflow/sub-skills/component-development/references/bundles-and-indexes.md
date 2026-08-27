# Bundles, Extensions, and Component Indexes

Langflow uses `lfx` for component runtime contracts and supports separately packaged extension bundles. Built-in components ship with the `lfx` package; extension bundles are pip-installable packages discovered by entry points and loaded at server startup.

## When to Use a Bundle

Use an extension bundle when components should be distributed, versioned, or optionally installed independently from the core Langflow server. Good bundle candidates include provider integrations, tools with heavy optional dependencies, and components maintained on a separate release cadence.

Keep components in the core tree when they are foundational, dependency-light, or tightly coupled to built-in Langflow behavior.

## Extension Manifest

A bundle ships an `extension.json` next to its package code or declares the same metadata under `[tool.langflow.extension]` in `pyproject.toml`. If both exist, the loader prefers `extension.json`.

Minimal manifest:

```json
{
  "$schema": "https://schemas.langflow.org/extension/v1.json",
  "id": "lfx-my-extension",
  "version": "0.1.0",
  "name": "My Extension",
  "description": "Components for my integration.",
  "lfx": { "compat": ["1"] },
  "bundles": [
    { "name": "my_bundle", "path": "components/my_bundle" }
  ]
}
```

Top-level rules:

- `id` is required, globally unique, lowercase hyphenated, starts with a letter, and conventionally begins with `lfx-`.
- `version` is required and should be SemVer.
- `name` is required and appears in user-facing extension metadata.
- `description` is optional but should explain the integration.
- `lfx.compat` is required and must include the active bundle API version as a string, currently `"1"` for the verified Langflow line.
- `bundles` is required. Current v0 accepts exactly one bundle entry.
- `bundles[].name` is lowercase snake_case and becomes part of canonical component references such as `ext:my_bundle:MyComponent@official`.
- `bundles[].path` is relative to the manifest directory, must not be absolute, and must not contain `..`.
- `capabilities.requiresCredentials` can be set when the bundle's components generally require user credentials.

Reserved manifest keys such as `services`, `routes`, `hooks`, `starterProjects`, and `userConfig` are deferred. Setting them to non-null values is rejected with a dedicated deferred-field error.

## Pyproject Pattern

A package-style bundle should include the `langflow.extensions` entry point and ensure the manifest and component files are included in wheels/sdists.

```toml
[project]
name = "lfx-my-extension"
version = "0.1.0"
requires-python = ">=3.10,<3.15"
dependencies = [
  "lfx>=1.10.0.dev0,<2.0.0",
]

[project.entry-points."langflow.extensions"]
lfx-my-extension = "lfx_my_extension"

[tool.hatch.build.targets.wheel]
packages = ["src/lfx_my_extension"]
include = ["src/lfx_my_extension/extension.json", "src/lfx_my_extension/components/**/*.py"]
```

Practical packaging rules:

- The entry-point value should be the importable package containing the manifest.
- Ship `extension.json` inside the package so `importlib.metadata.files()` can discover it after installation.
- Include all component Python files in the wheel.
- Declare direct runtime dependencies in the bundle package, not only in the root Langflow package.
- Keep heavy provider stacks as optional extras when the component can run in a remote or degraded mode.
- Use platform markers for dependencies with unavailable wheels on some architectures.

## Component Reference Changes

Extension components use canonical IDs shaped like:

```text
ext:<bundle_name>:<ComponentClass>@official
```

A saved flow may still contain an older bare class reference. Langflow can rewrite known moved components when migration metadata is present, but future agents should still preserve old class/name identifiers and avoid ambiguous duplicate names across bundles.

If a flow reports `component-not-found-with-hint`, use the hinted canonical ID to identify the missing bundle and install or enable that package. If a flow reports `component-name-ambiguous`, choose the intended bundle and replace the reference with the canonical extension ID.

## Dynamic Loading with `LFX_DEV`

Langflow normally uses a prebuilt component index for fast startup. Development mode is controlled by `LFX_DEV`:

```bash
LFX_DEV=1 langflow run
LFX_DEV=true langflow run
LFX_DEV=mistral,openai langflow run
```

Semantics:

- Empty or unset `LFX_DEV`: production mode. Load built-in component index, then cache, then dynamic fallback.
- `LFX_DEV=1`, `true`, or `yes`: full dev mode. Rebuild all components dynamically so source changes are visible.
- `LFX_DEV=0`, `false`, or `no`: explicitly disable dev mode.
- `LFX_DEV=a,b,c`: selective dev mode. Load the index and dynamically reload only the named modules.

Use `LFX_DEV=1` while developing component classes or rebuilding the built-in component index. Use selective mode when full dynamic import is slow or provider modules import heavy dependencies.

## Component Index Rebuilds

The repository's component index builder imports all `lfx` components, normalizes deterministic metadata, strips dynamic fields such as timestamps, computes a SHA256 hash, and writes the formatted JSON index used for fast startup.

Typical command for a source checkout:

```bash
make build_component_index
```

Use this after adding or moving built-in `lfx` components, changing component metadata, or updating dynamic import maps. The maintained target runs the index builder with dynamic component loading. Do not use it as the first check for provider-heavy components; run static skeleton and targeted tests first.

Index behavior to know:

- The index version is compared to the installed `lfx` distribution version.
- The index contains metadata counts, sorted entries, and a `sha256` integrity field.
- If the built-in index is missing, invalid, version-mismatched, or hash-mismatched, Langflow falls back to cache or dynamic import.
- A rebuild can fail because one component imports an undeclared optional dependency at module import time. Fix the import/dependency issue instead of editing the index manually.

## Extension Validation Commands

Use these commands for bundle development:

```bash
lfx extension schema --output extension.schema.json
lfx extension validate path/to/extension/root
lfx extension list
lfx extension dev path/to/extension/root
```

Validation checks manifest shape, `lfx.compat`, bundle path safety, bundle path existence, deferred fields, and other typed errors. `extension list` shows installed/discovered extensions. `extension dev` is useful when iterating on a local extension root.

## Bundle Test Strategy

For a bundle migration or new extension:

1. Run static checks on every component file.
2. Validate the extension manifest.
3. Import the package root in a clean environment with only declared dependencies.
4. Run bundle unit tests that avoid credentials by mocking provider clients or using local fixtures.
5. Add integration tests only when they can skip cleanly without credentials or external services.
6. Rebuild the component index only for built-in component changes, not for third-party extension-only packages.

## Common Manifest Error Codes

- `manifest-invalid`: JSON/TOML shape failed validation; read the field named in the message.
- `manifest-not-found`: no `extension.json` and no `[tool.langflow.extension]` section were found at the extension root.
- `version-constraint-unsatisfied`: `lfx.compat` does not include the running bundle API version.
- `field-deferred-in-this-milestone`: a reserved future field was set to a non-null value.
- `multi-bundle-deferred-in-this-milestone`: more than one bundle entry was declared.
- `path-escape`: `bundles[].path` resolved outside the manifest root.
- `bundle-path-not-found`: `bundles[].path` does not point to an existing directory.

## Porting Checklist

When migrating an integration into an extension bundle:

- Keep the component class name stable unless creating a deliberate new component.
- Create a package such as `lfx_<bundle>` with `extension.json` next to `__init__.py`.
- Move component modules under `components/<bundle_name>/` and export them through that package's `__init__.py` if needed.
- Add `[project.entry-points."langflow.extensions"]` to the bundle `pyproject.toml`.
- Add direct runtime dependencies to the bundle package.
- Validate the extension root with `lfx extension validate`.
- Confirm installed discovery with `lfx extension list` or a small import probe.
- Add migration metadata for old saved-flow references when moving a previously built-in component.
- Keep component tests and bundle tests focused, credential-safe, and marked/skipped when external services are required.
