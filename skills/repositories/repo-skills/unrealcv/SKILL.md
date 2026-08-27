---
name: "unrealcv"
description: "Routes UnrealCV tasks across the Python client, plugin build, and
  maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# UnrealCV

Use this skill for UnrealCV client workflows, plugin build/package workflows, and command/doc maintenance. The packaged source snapshot under `references/source-bundle.md` keeps the build and maintenance routes self-contained when the original checkout is unavailable.

## Install and inspect

- Public install: `pip install unrealcv`
- Self-contained editable install from the packaged client snapshot: `pip install -e references/unrealcv-source/client/python`
- Minimal import check: `python -c "import unrealcv; print(unrealcv.__version__)"`
- Packaged source snapshot: `references/source-bundle.md` and `references/unrealcv-source/`

Read `references/repo-provenance.md` before deciding whether this skill matches the current checkout, and read `references/troubleshooting.md` when installs, connection setup, or version/capability checks fail.

## Route map

### `sub-skills/python-client/`
Use this when the task is about connecting to a running UnrealCV server, sending `vget`/`vset`/`vbp`/`vexec` commands, decoding image or depth payloads, using `UnrealCv_API`, working with `Client`/`SocketMessage`/`ApiVersionManager`, or launching local binaries through the Python runtime helpers.

Read these bundled files first:
- `sub-skills/python-client/references/api-reference.md` for the public Python API surface and command families.
- `sub-skills/python-client/references/workflows.md` for quick-start and live-server recipes.
- `sub-skills/python-client/references/troubleshooting.md` for connection, decoding, and capability failures.
- `sub-skills/python-client/scripts/local_client_smoke.py` for a safe dummy-server smoke check.

### `sub-skills/plugin-build/`
Use this when the task is about building, installing, or packaging the UnrealCV plugin or a game binary, or when a request mentions `build.py`, `UE4Automation`, `UnrealCV.uplugin`, `BuildPlugin`, `BuildCookRun`, or installing the plugin into a project or engine folder. The bundled helper uses `references/unrealcv-source/UnrealCV.uplugin` plus the packaged plugin `Config/`, `Content/`, `Resources/`, and `Source/` tree by default, so it does not need the original UnrealCV checkout.

Read these bundled files first:
- `references/source-bundle.md` for the packaged source snapshot layout.
- `sub-skills/plugin-build/references/workflows.md` for plugin install/build/package recipes.
- `sub-skills/plugin-build/references/troubleshooting.md` for Unreal Engine, UAT, and path issues.
- `sub-skills/plugin-build/scripts/build_plugin.py` for a safe wrapper around the packaged build flow.

### `sub-skills/maintenance/`
Use this when the task is about refreshing the public API snapshot, regenerating command schema docs, validating command coverage, or keeping generated docs aligned with code changes. The maintenance helpers default to the packaged source snapshot under `references/unrealcv-source/`, so they do not need the original checkout unless you explicitly point them at another root.

Read these bundled files first:
- `references/source-bundle.md` for the packaged source snapshot layout.
- `sub-skills/maintenance/references/workflows.md` for snapshot and schema refresh steps.
- `sub-skills/maintenance/references/troubleshooting.md` for stale-doc and coverage-drift failures.
- `sub-skills/maintenance/scripts/update_public_api_snapshot.py` for snapshot checks and refreshes.
- `sub-skills/maintenance/scripts/validate_command_coverage.py` for command-doc coverage checks.

## What this skill does not do

- It does not ask you to run the original repository's native examples or tests from the runtime skill.
- It does not depend on the current checkout being present for runtime use; bundled references and scripts are self-contained.
- It does not replace the generated sub-skill routes with raw prose when a bundled script is available.

## Before you change the skill

Read `references/repo-provenance.md` and compare the current checkout commit, branch, and package version to the snapshot. If they differ, refresh the skill instead of assuming it is current.
