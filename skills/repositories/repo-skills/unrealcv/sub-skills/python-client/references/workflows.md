# Python Client Workflows

## Purpose

Read this for quick-start recipes that combine connection setup, command requests, image decoding, and optional launcher helpers.

## Quick start

1. Install the package: `pip install unrealcv`
2. Import the client: `from unrealcv import Client, UnrealCv_API`
3. Connect to a running UnrealCV server or launch a local binary first.
4. Use `Client` for low-level requests or `UnrealCv_API` for higher-level camera/object/image helpers.

## Minimal request pattern

```python
from unrealcv import client
client.connect()
if client.isconnected():
    print(client.request('vget /unrealcv/status'))
```

Use this pattern when you need a quick connection check or a small command probe.

## High-level image workflow

- Create `UnrealCv_API(port, ip, resolution)`.
- Use `get_image`, `get_depth`, or `get_mask` for the camera output you need.
- Decode to arrays with the built-in image helpers.
- Use `save_image` when you want the server to write a file path instead of returning raw bytes.

## Object and camera workflow

- Read the current camera state with `get_cam_location`, `get_cam_rotation`, and `get_cam_pose`.
- Move a camera with `set_cam_location`, `set_cam_rotation`, and `set_cam_fov`.
- Enumerate objects with `get_objects`.
- Inspect or mutate objects with `get_obj_location`, `set_obj_location`, `get_obj_rotation`, `set_obj_rotation`, `get_obj_scale`, and `set_obj_scale`.
- Spawn or destroy scene objects with `spawn_object_from_path`, `set_new_obj`, and `destroy_obj`.

## Optional runtime launch workflow

Use the launcher helpers when you need the Python workflow to start the environment itself.

- `RunUnreal` starts a local binary or packaged game.
- `RunDocker` starts a containerized environment when Docker is available.
- `UE4Binary` is a small convenience wrapper for starting and stopping a platform-specific binary.

Typical flow:

1. Resolve the binary path.
2. Start the binary with the desired resolution and rendering flags.
3. Connect with `Client` or `UnrealCv_API`.
4. Run the commands you need.
5. Close the API/client and then stop the launcher helper.

## Safe local smoke workflow

When Unreal Engine is not available, use the bundled dummy-server smoke helper instead of a live scene.

- Start the local dummy server from `scripts/local_client_smoke.py`.
- Confirm that `Client` connects and request framing works.
- Use the same script to exercise payload decoding and command capability helpers.

## Troubleshooting checkpoints

- If `client.isconnected()` stays false, verify the server address and port.
- If the server advertises no command list, keep command-capability warnings advisory.
- If image decoding fails, verify the capture mode and the response format.
- If the launcher cannot find a binary or `unrealcv.ini`, recheck the binary path and Unreal environment layout.
