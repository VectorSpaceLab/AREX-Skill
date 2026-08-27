# Python Client Troubleshooting

## Purpose

Read this when a Python client workflow fails after the package imports successfully.

## Connection problems

### Symptom: `client.isconnected()` is false

**Likely causes**
- No UnrealCV server is running.
- The host or port is wrong.
- The binary has not finished starting yet.
- A second client already owns the connection.
- UDS was requested on a platform that does not support it.

**What to do next**
- Verify the server process or start the binary with the launcher helpers.
- Recheck the endpoint and retry with a longer timeout.
- Use the bundled dummy-server smoke helper if you only need to test transport.
- On Linux, confirm whether the workflow expects TCP or `/tmp/unrealcv_<port>.socket`.

### Symptom: `Request timed out`

**Likely causes**
- The server is slow to respond.
- The server is not actually listening on the port.
- The request was sent to a binary that is not ready yet.

**What to do next**
- Probe `vget /unrealcv/status` or `vget /unrealcv/version`.
- Increase the timeout only after confirming the endpoint is reachable.

## Capability and version problems

### Symptom: command-capability warnings

**Likely causes**
- `/vget /unrealcv/commands` is not available on the server.
- The server is older than the command-discovery threshold.

**What to do next**
- Treat the warning as advisory.
- Fall back to known stable routes or a version check.
- Do not claim unsupported routes as available unless the server advertises them.

### Symptom: UnrealZoo-only helper fails on a base server

**Likely causes**
- The connected server does not expose UnrealZoo/dev-only routes.

**What to do next**
- Confirm the server version and the available command list.
- Keep the task within the open-source command surface when the dev routes are absent.

## Decoding problems

### Symptom: image or depth decode returns `None`

**Likely causes**
- The response bytes are not PNG/NPY/BMP data.
- The requested mode does not match the returned payload.
- The server returned an error string instead of image bytes.

**What to do next**
- Use `read_png`, `read_npy`, or `MsgDecoder.decode_img` with the matching mode.
- Check the request string and confirm whether the server wrote to disk or returned bytes.

### Symptom: `MsgDecoder.decode_img` raises `ValueError`

**Likely causes**
- An unsupported image mode was passed.

**What to do next**
- Use one of the supported modes from the API reference and docs.

## Launcher problems

### Symptom: the launcher cannot find the binary or `unrealcv.ini`

**Likely causes**
- The binary path is wrong.
- The Unreal environment layout does not match the launcher expectations.
- `UnrealEnv` points to the wrong root.

**What to do next**
- Check the binary path and the generated `unrealcv.ini` path.
- Make sure the binary exists before starting the launcher.
- Use the launcher helper's path-reporting logic before attempting a full start.

### Symptom: Docker launch fails

**Likely causes**
- Docker is not installed or not running.
- The image name is wrong.
- GPU or display forwarding is not configured for the container.

**What to do next**
- Confirm the Docker daemon and image name.
- Start with the local dummy-server or local-binary path if Docker is unavailable.

## When to stop

- If the task needs a real Unreal Engine project and no compatible binary exists, move to the plugin-build sub-skill or narrow the task to client-only inspection.
- If the task only needs to prove the package is installed, use the bundled smoke helper and avoid live-server assumptions.
