---
name: "python-client"
description: "Routes UnrealCV Python client tasks for connecting to servers,
  sending commands, decoding responses, and launching local binaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Python Client

Use this sub-skill for anything that talks to a running UnrealCV server through the Python package. The runtime helpers are bundled here, but this route still operates against a live server or local dummy server rather than a packaged source snapshot.

## Read first

- `references/api-reference.md` for the verified public API surface, command families, and method groups.
- `references/workflows.md` for quick-start and live-server recipes.
- `references/troubleshooting.md` for connection, decoding, version, and launcher failures.
- `scripts/local_client_smoke.py` for a safe dummy-server smoke check.
- `scripts/connect_and_request.py` if you need a live-server request helper.
- `references/api-reference.md` for the public API surface and bundled install facts.

## What this sub-skill covers

- `Client`, `SocketMessage`, and `ApiVersionManager`
- `UnrealCv_API` camera, object, scene, image, capture, recording, pak, and panoramic helpers
- `MsgDecoder` and utility functions such as `read_png`, `read_npy`, and `parse_resolution`
- Data models from `unrealcv.models`
- Launcher helpers (`RunUnreal`, `RunDocker`, `UE4Binary`) when the client workflow also starts a binary
- Optional command-capability checks and UnrealZoo-only helpers when the connected server supports them

## Typical triggers

- "How do I connect to UnrealCV from Python?"
- "How do I request camera location, depth, or object data?"
- "How do I decode lit/depth/normal responses?"
- "How do I start a local binary or Dockerized Unreal environment and then connect?"
- "How do I handle command-capability warnings or version mismatches?"

## What belongs elsewhere

- Plugin build, install, or packaging requests belong in `../plugin-build/`.
- Refreshing the generated command schema or public API snapshot belongs in `../maintenance/`.
- Do not send future agents back to the original repo examples or tests for runtime use; use the bundled references and scripts instead.

## Usage pattern

1. Confirm the package is installed with `pip install unrealcv` or by using the bundled package snapshot under `../../references/unrealcv-source/client/python` when you want a self-contained inspection target.
2. Connect with `Client` for low-level transport or `UnrealCv_API` for high-level camera/object/image helpers.
3. Use `ApiVersionManager` when the task needs command discovery or version gating.
4. Use the bundled smoke helper before asking anyone to debug a live UnrealCV server.

## Failure modes to keep in mind

- No running server or wrong endpoint.
- Server too old to report supported commands.
- Image/depth payloads that do not match the requested mode.
- UDS only available on Linux and only after the binary creates its socket.
- Live launch helpers failing because the binary path or `unrealcv.ini` state is wrong.
