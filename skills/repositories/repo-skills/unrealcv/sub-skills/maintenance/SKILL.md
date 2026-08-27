---
name: "maintenance"
description: "Routes UnrealCV command-doc, public API snapshot, and
  coverage-maintenance tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Maintenance

Use this sub-skill when the repo changes and the generated command docs or public API snapshot need to be refreshed. The bundled helpers default to `../../references/unrealcv-source/`, so they do not need the original checkout unless you intentionally override the root.

## Read first

- `../../references/source-bundle.md` for the packaged source snapshot layout.
- `references/workflows.md` for snapshot and schema refresh steps.
- `references/troubleshooting.md` for drift, editor-only-route, and coverage issues.
- `scripts/update_public_api_snapshot.py` for the public API snapshot workflow.
- `scripts/validate_command_coverage.py` for command-doc coverage checks.
- `scripts/generate_command_schema.py` for schema regeneration when the command surface changes.

## What this sub-skill covers

- Refreshing the packaged `../../references/unrealcv-source/client/python/unrealcv/public_api_snapshot.json`
- Regenerating the packaged `../../references/unrealcv-source/docs/reference/command_schema.json` and related command docs
- Validating that the generated docs mention every runtime command
- Checking that the public API snapshot still matches the exported Python surface
- Distinguishing runtime commands from editor-only bindings

## Typical triggers

- "I added or removed a command handler; update the docs."
- "The public API snapshot is stale."
- "The generated command docs are missing a route."
- "Validate command coverage after changing the C++ or Python API surface."

## What belongs elsewhere

- Runtime client usage belongs in `../python-client/`.
- Plugin build, install, and packaging belong in `../plugin-build/`.
- Do not route a live-server debugging task here just because it touches command names.

## Usage pattern

1. Refresh the generated snapshot or schema with the bundled helper.
2. Re-run the coverage check.
3. Review any runtime-versus-editor mismatch before declaring the docs current.
4. Only pass `--repo-root` when you intentionally want to inspect another checkout instead of the packaged snapshot.
