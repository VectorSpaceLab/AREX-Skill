# Maintenance Workflows

## Purpose

Read this when the UnrealCV command surface changes and you need to refresh the generated command schema, public API snapshot, or command-coverage checks.

## Quick start

The executable entrypoints default to the packaged source snapshot at `../../references/unrealcv-source/`, so they do not need an external UnrealCV checkout.

1. Confirm the packaged source snapshot location in `../../references/source-bundle.md`.
2. Refresh or check the public API snapshot:
   ```bash
   python scripts/update_public_api_snapshot.py --check
   ```
   If it reports drift, rerun the same command without `--check`.
3. Regenerate the command schema and generated docs:
   ```bash
   python scripts/generate_command_schema.py
   ```
4. Validate the generated docs and snapshot together:
   ```bash
   python scripts/validate_command_coverage.py --strict
   ```

## Public API snapshot workflow

Use `scripts/update_public_api_snapshot.py` when Python exports change in the packaged `../../references/unrealcv-source/client/python/unrealcv/*.py` tree.

- It scans the packaged Python client source with AST only.
- It writes `../../references/unrealcv-source/client/python/unrealcv/public_api_snapshot.json` by default.
- `--check` is the safest first step because it fails without rewriting files.
- Pass `--repo-root /path/to/unrealcv` only when intentionally checking another checkout.

## Command schema workflow

Use `scripts/generate_command_schema.py` after adding, removing, or renaming command registrations in the packaged `../../references/unrealcv-source/Source/UnrealCV/Private/**/*.cpp` tree.

- It regenerates `../../references/unrealcv-source/docs/reference/command_schema.json` by default.
- It also rewrites `../../references/unrealcv-source/docs/reference/commands_generated.rst.txt` by default.
- Editor-only command registrations remain marked as editor-only in the generated schema.
- Use `--output` and `--rst-output` for temporary files when you want a non-mutating comparison.

## Coverage validation workflow

Use `scripts/validate_command_coverage.py --strict` before declaring the docs current.

- It compares the packaged schema and generated RST against the packaged C++ command source.
- It checks that the packaged public API snapshot still matches the packaged Python surface.
- It reports whether the bundled hand-written Python API docs still mention the expected package imports and autodoc setup.

## Safe checks

- Start with `--help` on any bundled script if you are unsure about its arguments.
- Prefer `--check` or a dry-run-style validation before rewriting files.
- Review the generated JSON/RST output before committing if the command parser touched a large portion of the command surface.
- Do not rely on the caller's current working directory for source files; use the packaged snapshot defaults or pass an explicit `--repo-root`.

## When to stop and switch tasks

- If the change is only about runtime client usage, switch to `../python-client/`.
- If the change is only about building or packaging the plugin, switch to `../plugin-build/`.
- If a command registration change is actually a source-code bug, fix the source first and then rerun these maintenance helpers.