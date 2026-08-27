# Plugin Build Workflows

## Purpose

Read this for the UnrealCV plugin build, install, and packaging paths.

## Build the plugin from the packaged `.uplugin`

The executable entrypoint is `scripts/build_plugin.py`. It defaults to the bundled source snapshot at `../../references/unrealcv-source/` and uses the packaged `UnrealCV.uplugin`, `Config/`, `Content/`, `Resources/`, and `Source/` tree. It does not need an external UnrealCV checkout.

Typical commands:

```bash
# Inspect the packaged build command without running Unreal Automation Tool.
python scripts/build_plugin.py --dry-run

# Build the packaged plugin with an explicit Unreal Engine root.
python scripts/build_plugin.py --ue4 /path/to/UE_5.6 --output ./Plugins/UnrealCV --execute

# Target a different source checkout only when that is intentional.
python scripts/build_plugin.py --source-root /path/to/unrealcv --ue4 /path/to/UE_5.6 --execute
```

The wrapper defaults to dry-run behavior unless `--execute` is passed. Relative descriptor names are resolved inside the packaged source snapshot before the caller's current directory.

## Install the plugin into a project or engine

Two install targets are common:

- Project install: copy `UnrealCV/` into `<Project>/Plugins/`
- Engine install: copy `UnrealCV/` into `<UE>/Engine/Plugins/`

Concrete self-contained entrypoints:

```bash
# Copy the bundled source plugin into a project Plugins folder without building.
python scripts/build_plugin.py --copy-plugin-source-to /path/to/MyProject --execute

# Build first, then copy the built output into a project/engine/Plugins target.
python scripts/build_plugin.py --ue4 /path/to/UE_5.6 --output ./Plugins/UnrealCV --install-target /path/to/MyProject --execute
```

After installation, confirm that the plugin is enabled in the editor and that the project is in play mode before trying UnrealCV commands.

## Package a game binary

When a user wants an UnrealCV-enabled distributable binary:

1. Ensure packaged-game viewmode support is configured:
   ```bash
   python scripts/build_plugin.py --configure-console-variables /path/to/UE_5.6 --execute
   ```
   This ensures `r.ForceDebugViewModes = 1` in `Engine/Config/ConsoleVariables.ini`.
2. Package the `.uproject` with the build wrapper or the editor:
   ```bash
   python scripts/build_plugin.py /path/to/MyProject/MyProject.uproject --ue4 /path/to/UE_5.6 --output ./UE4Binaries/MyProject --execute
   ```
3. Copy or publish the resulting binary as appropriate for the target platform.

## Developer command-extension workflow

To add or modify UnrealCV commands in the packaged source snapshot:

1. Edit or copy the relevant command handler under `../../references/unrealcv-source/Source/UnrealCV/Private/Commands/`.
2. Recompile the plugin or the C++ project with `scripts/build_plugin.py`.
3. Re-run the build or packaging step.
4. Refresh the command documentation and API snapshot with the maintenance sub-skill if the command surface changed.

## Safe checks

- Use `scripts/build_plugin.py --help` to inspect supported arguments.
- Use a dry-run invocation first if the engine path is unknown.
- Confirm output folder selection before any overwrite.
- Do not point future agents at the original repository checkout unless `--source-root` is explicitly needed for a different target checkout.
