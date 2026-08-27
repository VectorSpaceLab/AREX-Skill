# Troubleshooting

## Purpose

Read this when an UnrealCV workflow fails before you know which sub-skill owns the problem. For workflow-specific failures, prefer the nearest sub-skill troubleshooting file first.

## Quick checks

1. Confirm the package imports: `python -c "import unrealcv; print(unrealcv.__version__)"`
2. Confirm the Python install path is the one you expect.
3. Check that the UnrealCV server or binary is actually running before sending commands.
4. If the task uses the plugin, confirm the Unreal Engine path and use the packaged source snapshot in `references/unrealcv-source/` unless you intentionally override it.

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: unrealcv` | The Python package is not installed in the target environment, or the wrong interpreter is active | Reinstall with `pip install unrealcv`, or use the bundled package snapshot at `references/unrealcv-source/client/python` for self-contained inspection, then re-run the import check |
| `ImportError` for `opencv-python`, `pillow`, `numpy`, `pydantic`, or `docker` | The Python dependencies were not installed with the package or the environment is incomplete | Reinstall the package into the target environment and run `python -m pip check` |
| `UnrealCV server is not running` / `client.isconnected() == False` | No live UnrealCV server is listening, the host/port is wrong, or the binary has not finished starting | Check the server process, port, and whether the task should use a live binary, `RunUnreal`, or dummy-server smoke instead |
| `Request timed out` | The binary is slow to start, the port is wrong, or the request hit a server that does not respond | Recheck the endpoint and retry with a longer timeout only after confirming the server is reachable |
| `The connected UnrealCV server is too old to report its supported commands` | `/unrealcv/commands` is unavailable on the connected server | Treat capability checks as advisory and avoid route claims that depend on command discovery |
| `The connected UnrealCV server may not support command ...` | The request targets a route that the connected server does not advertise | Verify the command against `vget /unrealcv/commands` or the command schema docs |
| Image or depth decoding returns `None` | The payload is not a PNG/NPY/BMP blob or the mode argument is wrong | Use the matching decoder (`read_png`, `read_npy`, or `MsgDecoder.decode_img`) and verify the response bytes |
| `UnrealEnv environment variable not set` | The launcher fell back to the default UnrealEnv path | Set `UnrealEnv` explicitly or pass an explicit binary path into the launcher helper |
| Plugin build complains about `RunUAT` or Unreal Engine paths | The Unreal Engine installation is missing or the engine path is wrong | Switch to the plugin-build sub-skill and verify the engine root, UAT path, and build target |

## When to stop and change scope

- If the task requires Unreal Engine but no compatible engine install is available, use the client-only workflows or narrow the task to package inspection and docs maintenance.
- If the task requires a live UnrealCV server and none is running, use the dummy-server smoke helper or choose a workflow that does not need the game binary.
- If a failure comes from editor/build tooling rather than the Python client, route to `sub-skills/plugin-build/`.

## Useful follow-up files

- `sub-skills/python-client/references/troubleshooting.md`
- `sub-skills/plugin-build/references/troubleshooting.md`
- `sub-skills/maintenance/references/troubleshooting.md`
