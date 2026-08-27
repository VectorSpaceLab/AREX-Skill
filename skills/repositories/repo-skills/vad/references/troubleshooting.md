# Cross-cutting VAD troubleshooting

## Install/import

- **Missing `mmcv`, `mmdet`, `mmseg`, `mmdet3d`, or version conflicts:** use the documented legacy family as a coordinated set. Check versions before changing packages; do not combine current MMDetection3D with the old VAD configs without a compatibility plan.
- **`ball_query_ext` or another `*_ext` import error:** native MMDetection3D extensions are absent, partially built, or ABI-incompatible. Check CUDA toolkit/driver, compiler, PyTorch ABI, and the exact MMDetection3D checkout/version. A CPU-only import cannot prove CUDA VAD support.
- **CUDA unavailable:** check the driver, CUDA-enabled PyTorch, visible devices, and GPU architecture. VAD's actual detector runtime has no truthful CPU substitute in this skill.
- **Plugin registry `KeyError`:** confirm the selected config has `plugin=True` and the plugin package is importable before builders resolve custom types. A config parser can pass while the plugin import fails later.

## Data/config

- **Missing temporal PKLs or map JSON:** use `data-preparation`'s checker and align `data_root`, `ann_file`, `map_ann_file`, and the actual VAD-specific filenames.
- **Stock nuScenes PKL used:** regenerate with the VAD converter; the dataset expects temporal history/future, ego, CAN-bus, and vector-map fields.
- **Stage mismatch:** pair tiny with tiny and base with base; stage 2 expects the corresponding stage-1 checkpoint through `load_from`.
- **Geometry/tensor mismatch:** keep point range, voxel size, BEV dimensions, map vector point counts, queue length, and temporal annotation generation consistent.

## CLI/runtime

- Run config/result/data preflights before expensive commands.
- Use only one of deprecated/replacement flag pairs (`--options` vs `--cfg-options`; `--options` vs `--eval-options`). Quote nested list/tuple overrides.
- Evaluate with one GPU and `--launcher none`; the project warns that distributed evaluation can be inaccurate.
- For released weights, use the legacy image normalization documented in `training-evaluation`; otherwise metrics and visualizations can be wrong.

## External limits

Full nuScenes/CAN-bus acquisition, checkpoint downloads, training, evaluation, and rendering are not performed by bundled helpers. If credentials, network, large storage, GPU capacity, or codecs are missing, report the specific prerequisite and stop rather than fabricating a successful result.
