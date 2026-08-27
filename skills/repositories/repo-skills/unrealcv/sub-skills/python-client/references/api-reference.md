# UnrealCV Python API Reference

## Purpose

Read this when you need verified Python API names, signatures, or command families for the UnrealCV client package.

## Verified package facts

- Distribution: `UnrealCV`
- Import package: `unrealcv`
- Version inspected: `1.2.0`
- Python requirement: `>=3.9`
- Runtime dependencies from package metadata: `docker`, `numpy`, `opencv-python`, `pillow`, `pydantic`
- Bundled editable-install snapshot: `../../references/unrealcv-source/client/python`

## Top-level exports

`unrealcv.__all__` exposes the main client entry points:

- `Client`
- `SocketMessage`
- `ApiVersionManager`
- `__version__`

The package also re-exports the launcher, automation, API, and utility symbols from its modules.

## Verified signatures

| Symbol | Signature |
| --- | --- |
| `Client` | `(endpoint, type='inet')` |
| `SocketMessage` | `(payload)` |
| `ApiVersionManager` | `(request)` |
| `UnrealCv_API` | `(port, ip, resolution, mode='tcp')` |
| `MsgDecoder` | `()` |
| `UE4Automation` | `(engine)` |
| `RunUnreal` | `(ENV_BIN, ENV_MAP=None)` |
| `RunDocker` | `(path2env, image='zfw1226/unreal:latest')` |
| `ResChecker` | `()` |

Key utility signatures:

| Function | Signature |
| --- | --- |
| `read_png` | `(res)` |
| `read_npy` | `(res)` |
| `parse_resolution` | `(res)` |
| `get_path2UnrealEnv` | `()` |
| `measure_fps` | `(func, *args, **kwargs)` |
| `convert2planedepth` | `(PointDepth, f=320)` |

## Command families

The source command bindings and generated schema show roughly 133 commands, with 129 runtime routes and 4 editor-only routes.

### Core runtime families

| Family | Representative commands | Notes |
| --- | --- | --- |
| Server info | `vget /unrealcv/status`, `vget /unrealcv/help`, `vget /unrealcv/commands`, `vget /unrealcv/version`, `vget /scene/name` | Used for availability and capability checks |
| Camera state | `vget /camera/[uint]/location`, `vset /camera/[uint]/location`, `vget /camera/[uint]/rotation`, `vset /camera/[uint]/rotation`, `vget /camera/[uint]/fov`, `vset /camera/[uint]/fov` | Location/rotation/FOV and camera metadata |
| Image capture | `vget /camera/[uint]/lit [str]`, `vget /camera/[uint]/depth [str]`, `vget /camera/[uint]/normal [str]`, `vget /camera/[uint]/object_mask [str]`, plus `_shared` variants | Uses PNG/NPY/BMP/bitmap helpers and optional shared-memory routes |
| Panoramic capture | `vget /camera/[uint]/panoramic ...` and modality-specific panoramic helpers | Includes `capture_panoramic`, `capture_panoramic_depth`, `capture_panoramic_mask`, `capture_panoramic_normal` |
| Object manipulation | `vget /objects`, `vget /object/[str]/location`, `vset /object/[str]/location`, `vget /object/[str]/rotation`, `vset /object/[str]/rotation`, `vset /object/[str]/show`, `vset /object/[str]/hide`, `vset /object/[str]/destroy` | Object query/mutation and visibility control |
| Object attributes | `vget /object/[str]/color`, `vset /object/[str]/color`, `vget /object/[str]/bounds`, `vget /object/[str]/bones`, `vget /object/[str]/scale`, `vset /object/[str]/scale` | Object inspection and geometry helpers |
| Scene/occupancy | `vget /scene/occupancy ...`, `vget /scene/occupancy/spec ...` | UnrealZoo-style occupancy helpers need supported server routes |
| Recording | `vget /record/...`, `vset /record/...`, `start_simple_recording`, `stop_recording` | Recording helpers and flags |
| Paks and assets | `vget /pak/...`, `vset /pak/...`, `mount_pak`, `unmount_pak`, `load_pak_asset`, `scan_pak_assets` | Asset-pack workflows |
| Blueprint execution | `vbp [obj_name] [func_name] ...`, `vexec ...`, `vcmd ...` | Blueprint and command execution helpers |
| Runtime control | `vset /pause`, `vset /resume`, `vget /action/game/is_paused`, `vset /camera/[uint]/size`, `vset /camera/[uint]/set_camera_fast_capture` | Server/game control helpers |

### Editor-only routes

The command schema marks these as editor-only:

- `vget /object/[str]/label`
- `vget /object/[str]/material`
- `vset /object/[str]/label [str]`
- `vset /object/[str]/material [uint] [str]`

## Major class groups

### `Client`

Use for low-level transport and request framing.

- `connect(timeout=1, start_receive_thread=True)`
- `request(message, timeout=5)`
- `request_batch(batch)`
- `receive()`
- `request_async(...)` and `request_batch_async(...)` are available in the source and tests for non-blocking paths

Transport details:

- TCP is the default.
- Linux UDS can be used when the server creates `/tmp/unrealcv_<port>.socket`.
- The client enforces message IDs and message framing through `SocketMessage`.

### `ApiVersionManager`

Use when the task needs command discovery or version gating.

- `load(timeout=5)`
- `get_server_version(timeout=5)`
- `get_server_version_tuple(timeout=5)`
- `supports_command(command)`
- `warn_if_command_maybe_unsupported(command)`
- `warn_unrealcv_plus_if_unsupported()`

Capability rules:

- Missing `/unrealcv/commands` disables capability checks but does not block requests.
- Commands that are not advertised may still work; the warning is advisory.
- `is_unrealcv_plus()` is true only when the server version meets the UnrealZoo threshold.

### `MsgDecoder`

Use for decoding response payloads.

Important methods:

- `decode_img(res, mode, inverse=False)`
- `decode_png(res)`
- `decode_npy(res)`
- `decode_depth(res, inverse=False)`
- `decode_bmp(res)`
- `decode_vertex(res)`
- `decode_color`, `decode_vector`, and related string helpers

Decoder notes:

- `read_png` and `MsgDecoder.decode_png` are for PNG bytes.
- `read_npy` and `MsgDecoder.decode_npy` are for NPY bytes.
- Invalid bytes return `None` or raise a decode error depending on the helper.

### `UnrealCv_API`

Use this for the high-level camera/object/scene API.

Verified method families from the source snapshot:

- Camera discovery and configuration: `get_camera_num`, `get_camera_list`, `get_camera_config`, `set_cam_location`, `set_cam_rotation`, `set_cam_fov`, `set_camera_fast_capture`
- Image capture: `get_image`, `get_image_multicam`, `get_image_multimodal`, `get_img_batch`, `get_depth`, `get_mask`, `save_image`
- Object queries and mutation: `get_objects`, `get_obj_location`, `set_obj_location`, `get_obj_rotation`, `set_obj_rotation`, `get_obj_scale`, `set_obj_scale`, `get_obj_bboxes`, `get_obj_bones`, `spawn_object_from_path`, `destroy_obj`
- Scene and visibility: `set_map`, `set_hide_obj`, `set_show_obj`, `set_hide_objects`, `set_show_objects`, `get_is_paused`, `set_pause`, `set_resume`
- Recording and capture: `start_simple_recording`, `stop_recording`, `set_recording_paused`, `set_record_via_viewport`, `set_record_add_timestamp`
- Panoramic capture: `capture_panoramic`, `capture_panoramic_depth`, `capture_panoramic_mask`, `capture_panoramic_normal`
- UnrealZoo/shared-memory extensions: `get_scene_occupancy`, `get_scene_occupancy_spec`, `get_optical_flow`, `get_camera_fast_capture`, `get_mounted_paks`, `mount_pak`, `unmount_pak`, `scan_pak_assets`
- Utility and introspection helpers: `batch_cmd`, `build_color_dict`, `build_pose_dic`, `camera_info`, `check_connection`, `config_ue`, `message_handler`, `supports_command`, `is_unrealcv_plus`

Use `return_cmd=True` when you want the command string without sending it.

### Launcher helpers

`RunUnreal`, `RunDocker`, and `UE4Binary` are used when the Python workflow also needs to start a local binary or Dockerized environment.

- `RunUnreal.start(docker=False, resolution=(640, 480), display=None, opengl=False, offscreen=False, nullrhi=False, gpu_id=None, local_host=True, sleep_time=8, log_file_path=None)`
- `RunUnreal.close()`
- `RunDocker.start(ENV_BIN=..., ENV_DIR_DOCKER='/UnrealEnv', options='', host_net=False)`
- `RunDocker.close()`

`UE4Automation` is the build/package wrapper used by the plugin-build workflow, but it is also visible here because it is part of the Python client package.

## When to use bundled scripts

- Use `scripts/local_client_smoke.py` to test the client transport without Unreal Engine.
- Use `scripts/connect_and_request.py` when you want a live-server request helper.
- Use `scripts/update_public_api_snapshot.py` or `scripts/validate_command_coverage.py` from the maintenance sub-skill when changing commands or public exports.
