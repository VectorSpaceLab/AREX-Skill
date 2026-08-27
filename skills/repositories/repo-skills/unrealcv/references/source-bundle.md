# UnrealCV Source Bundle

## Purpose

This skill ships a packaged UnrealCV source snapshot under
`references/unrealcv-source/` so the plugin-build and maintenance routes can run
without the original UnrealCV checkout.

## What is bundled

`source-bundle-manifest.json` records the exact packaged files, sizes, and SHA-256 hashes. The snapshot includes the files those routes need at runtime, including:

- `build.py`
- `UnrealCV.uplugin`
- `Config/`
- `Content/`
- `Resources/`
- `Source/UnrealCV/`
- `client/python/unrealcv/`
- `client/python/pyproject.toml`
- `client/python/tools/update_public_api_snapshot.py`
- `docs/conf.py`
- `docs/plugin/`
- `docs/reference/`

## How the bundled helpers use it

- `sub-skills/plugin-build/scripts/build_plugin.py` uses the packaged
  `UnrealCV.uplugin`, `Config/`, `Content/`, `Resources/`, and `Source/`
  tree from this directory by default. `build.py` is included as provenance
  for the original build flow.
- `sub-skills/maintenance/scripts/update_public_api_snapshot.py` and
  `sub-skills/maintenance/scripts/generate_command_schema.py` default to this
  directory as their repo root.
- `sub-skills/maintenance/scripts/validate_command_coverage.py` compares the
  bundled docs and snapshots against the bundled source snapshot by default.

## When to override the bundle

Pass `--source-root` or `--repo-root` only when you intentionally want to work
against another UnrealCV checkout.