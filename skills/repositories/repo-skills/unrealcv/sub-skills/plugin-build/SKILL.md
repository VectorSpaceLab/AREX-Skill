---
name: "plugin-build"
description: "Routes UnrealCV plugin build, install, and packaging tasks for
  Unreal Engine projects and binaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Plugin Build

Use this sub-skill when the task is about building, installing, or packaging the UnrealCV plugin or a game binary. The bundled build helper uses `../../references/unrealcv-source/UnrealCV.uplugin` plus the packaged `Config/`, `Content/`, `Resources/`, and `Source/` tree by default, so it can run without the original checkout.

## Read first

- `../../references/source-bundle.md` for the packaged source snapshot layout.
- `references/workflows.md` for build, install, and packaging recipes.
- `references/troubleshooting.md` for Unreal Engine, UAT, and path problems.
- `scripts/build_plugin.py` for a safer wrapper around the packaged build flow.

## What this sub-skill covers

- `build.py` argument behavior and the `UE4Automation` wrapper
- Building the plugin from a `.uplugin`
- Installing a built plugin into a project `Plugins/` folder or `Engine/Plugins/`
- Packaging a `.uproject` into a binary with UnrealCV embedded
- Developer workflows for modifying command handlers and recompiling the plugin

## Typical triggers

- "How do I build the UnrealCV plugin?"
- "How do I install UnrealCV into my UE project?"
- "How do I package a game binary with UnrealCV embedded?"
- "How do I compile the plugin after changing a command handler?"

## What belongs elsewhere

- Live Python client usage, request helpers, image decoding, and launcher state belong in `../python-client/`.
- Command-schema refreshes and public API snapshot maintenance belong in `../maintenance/`.
- Do not depend on the original repository checkout at runtime; use the bundled reference and script paths instead.

## Usage pattern

1. Confirm the Unreal Engine root or the project/plugin path.
2. Use the bundled build wrapper; it resolves `../../references/unrealcv-source/` by default, and `--source-root` is only needed when you intentionally target another checkout.
3. Install or package only after the build target and output path are clear.
4. Revisit the troubleshooting notes if Unreal Engine path discovery or packaging fails.
