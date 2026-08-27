# Maintenance Troubleshooting

## Purpose

Read this when a command-schema refresh, public API snapshot update, or coverage validation fails.

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `Public API snapshot is out of date` | Python exports changed in the packaged `../../references/unrealcv-source/client/python/unrealcv/*.py` tree | Rerun `scripts/update_public_api_snapshot.py` without `--check` and review the new packaged snapshot |
| `Public API snapshot is missing` | The packaged snapshot file was deleted or never generated | Regenerate it with `scripts/update_public_api_snapshot.py` |
| `Generated docs are missing commands` | A command binding was added, removed, or renamed without rerunning the schema generator | Run `scripts/generate_command_schema.py` and inspect the changed packaged `docs/reference/commands_generated.rst.txt` |
| `Schema and generated RST differ` | The packaged source tree changed after the docs were generated, or the command parser missed a binding | Re-run the generator and check the packaged command registration macros in `../../references/unrealcv-source/Source/UnrealCV/Private/**/*.cpp` |
| `Validator reports the snapshot differs from the current source` | The packaged snapshot is stale or the wrong `--repo-root` override was used | Confirm whether you meant the packaged root or an explicit external root, then rerun the snapshot update helper |
| A command appears in C++ but not in the schema | The command registration is hidden behind a parser edge case or a new macro shape | Inspect the `BindCommand` call site and extend the generator only if the new pattern is intentional |
| A command is marked editor-only unexpectedly | The registration sits under a `WITH_EDITOR` guard | Decide whether the command should stay editor-only and regenerate the docs accordingly |
| `python -c "import unrealcv"` fails while the scripts run | The active interpreter does not see the package install | Maintenance helpers use AST by default and do not require package import; only reinstall if the task also needs live package execution |

## What to check first

1. Confirm the helper is using the packaged root `../../references/unrealcv-source/` unless an explicit `--repo-root` override is intended.
2. Confirm the packaged source command registration lives under `../../references/unrealcv-source/Source/UnrealCV/Private/`.
3. Confirm the generated files are not being edited by hand.
4. If you intentionally target another checkout, pass `--repo-root` explicitly and keep its outputs separate from the packaged snapshot when appropriate.

## When to stop and switch sub-skills

- If the request is really about connecting to a running server or decoding payloads, use `../python-client/`.
- If the request is really about packaging or installing the plugin, use `../plugin-build/`.
- If the generator cannot parse a brand-new C++ command pattern, fix the source or narrow the scope before claiming the docs are current.