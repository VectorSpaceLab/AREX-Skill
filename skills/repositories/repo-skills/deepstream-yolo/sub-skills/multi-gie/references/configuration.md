# Multi-GIE configuration reference

## Duplicated config files

Each detector should keep its own copy of the inference config and the custom inference library folder.

## Key fields to change

| Key | Primary GIE | Secondary GIE | Notes |
| --- | --- | --- | --- |
| `gie-unique-id` | `1`, `2`, ... | unique per detector | Must be distinct across all GIEs |
| `process-mode` | `1` | `2` | Primary vs secondary inference |
| `operate-on-gie-id` | usually unset | the primary detector's `gie-unique-id` | Ties the secondary detector to the detector it should read from |
| `operate-on-class-ids` | usually unset | optional | Restrict secondary inference to a class subset |
| `config-file` | points at the primary config | points at the copied secondary config | Keep the file paths inside the owning `gieN/` folder |
| `model-engine-file` | per-detector engine cache | per-detector engine cache | Engines should live in the same `gieN/` folder as their config |
| `onnx-file` / `custom-network-config` / `model-file` | prefixed with `gieN/` in the scaffold | prefixed with `gieN/` in the scaffold | Relative paths are resolved from the runtime root when launching `deepstream-app` |
| `custom-lib-path` | `gieN/nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so` | same pattern | Each GIE uses its own rebuilt custom parser library |

## Plugin versioning

- The scaffold helper changes `YOLOLAYER_PLUGIN_VERSION` in each copied `yoloPlugins.h` so the detectors do not collide.
- Keep the version number aligned with the folder index when manually editing: `gie2` -> `2`, `gie3` -> `3`, and so on.

## Practical defaults

- Primary detector: `process-mode=1`
- Secondary detector: `process-mode=2`
- Secondary detector should usually point at the first detector with `operate-on-gie-id=1` unless the user intentionally nests the inference chain differently.
