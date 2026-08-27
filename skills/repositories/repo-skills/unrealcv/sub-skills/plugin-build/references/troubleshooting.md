# Plugin Build Troubleshooting

## Purpose

Read this when a plugin build, install, or packaging task fails.

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `RunUAT` or UAT path not found | The Unreal Engine root is wrong or incomplete | Verify the engine root and the platform-specific `Engine/Build/BatchFiles/RunUAT.*` path; the helper can still dry-run from the packaged source without UE |
| Plugin build silently targets the wrong folder | The output path was not the one you intended | Re-run `scripts/build_plugin.py --dry-run` and confirm the packaged descriptor plus output path first |
| Descriptor unexpectedly resolves to the caller's checkout | A relative path was passed and an override root was intended | Use the default packaged descriptor, pass an absolute descriptor path, or pass `--source-root` intentionally |
| Existing plugin folder is not overwritten | The overwrite flag was not passed | Decide whether to keep the existing build or explicitly request `--overwrite` |
| Editor crashes after installing the plugin | Plugin installation is incomplete, the source plugin was copied to the wrong target, or engine/project configuration is stale | Recheck the plugin copy target with `--copy-plugin-source-to` or `--install-target`, engine/project version, and crash logs |
| Packaged binary does not respond to UnrealCV commands | The packaged project is missing the UnrealCV configuration change or the build did not embed the plugin correctly | Run `scripts/build_plugin.py --configure-console-variables /path/to/UE --execute` and confirm `ConsoleVariables.ini` contains `r.ForceDebugViewModes = 1` |
| Linux build or run fails with OpenGL/library errors | The system OpenGL stack or required packages are missing | Follow the Linux-specific notes in the docs and verify the graphics stack before retrying |
| macOS build complains about the SDK or packaging path | The local Xcode/SDK setup is incomplete | Recheck the macOS prerequisites in the installation docs |

## When to stop

- If Unreal Engine is not installed, keep the task at dry-run, packaged-source copy, or path validation only.
- If the request is about client-side Python requests rather than build/package work, switch to `../python-client/`.
- If the request is about docs or snapshot maintenance, switch to `../maintenance/`.
