# Architecture/configuration troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `KeyError: VAD`/`VADHead`/custom coder | Plugin package was not imported before the OpenMMLab builder, or `plugin_dir` is wrong | Confirm `plugin=True`, keep the plugin directory importable from the process working directory, and use the config checker. Do not add arbitrary registry aliases. |
| `ImportError` for `ball_query_ext`, `iou3d_cuda`, or another `*_ext` | MMDetection3D native extensions are absent or built against an incompatible compiler/CUDA/PyTorch ABI | Treat as an environment gate. Install/build the exact compatible framework family and verify extensions before model construction; a config parse does not substitute for this. |
| Config parses but model build fails with an unknown nested type | A component is defined in a plugin module that was not loaded, or a VADv2/v1 config was mixed | Compare the selected family and plugin import order; inspect the registered class source and keep the matching config/model files together. |
| Stage-2 starts with missing checkpoint | `load_from` still points to the stage-1 file, or tiny/base families were mixed | Train or supply the matching stage-1 checkpoint, then update `load_from` to a valid path. Do not use a base checkpoint for tiny or vice versa. |
| Tensor shape or temporal history error | `queue_length`, BEV dimensions, point range, map point counts, and annotations disagree | Compare all dependent config keys and temporal PKL fields; regenerate data if the annotation contract is stale. |
| CAN-bus shift/rotation failure | `use_can_bus=True` but generated infos lack the expected ego/CAN-bus fields | Use VAD temporal conversion and the CAN-bus expansion; route raw data repair to [data-preparation](../../data-preparation/SKILL.md). |
| Visually wrong results with released weights | Current normalization differs from the legacy training normalization | Use the documented legacy `img_norm_cfg` for released checkpoint reproduction; see [training-evaluation](../../training-evaluation/SKILL.md). |
