# VAD configuration reference

## Common geometry and labels

The checked VAD config families define the following common contract unless a variant says otherwise:

| Key | Value/role |
|---|---|
| `point_cloud_range` | `[-15.0, -30.0, -2.0, 15.0, 30.0, 2.0]`; geometry-dependent model and assigner setting |
| `voxel_size` | `[0.15, 0.15, 4]` |
| detection classes | 10 nuScenes classes: car, truck, construction_vehicle, bus, trailer, barrier, motorcycle, bicycle, pedestrian, traffic_cone |
| map classes | `divider`, `ped_crossing`, `boundary` |
| map vectors/points | 100 vectors, 20 fixed points per GT/predicted line |
| BEV | `bev_h_=100`, `bev_w_=100` |
| object queries | `num_query=300` |
| temporal input | `queue_length=3` in tiny configs and `4` in base configs; inspect the selected file |
| modality | camera enabled, lidar/radar/map disabled in the listed VAD configs, external/CAN-bus features enabled |

If changing point-cloud range, update every dependent model, coder, assigner, and map geometry field. If changing fixed point counts, update both GT and prediction settings.

## Variant selection

- `VAD_tiny_stage_1.py` and `VAD_base_stage_1.py`: perception and prediction pretraining. Tiny uses 12 epochs in the checked config; base uses 24 epochs.
- `VAD_tiny_stage_2.py` and `VAD_base_stage_2.py`: planning stage, with `load_from` pointing to the corresponding stage-1 checkpoint and longer planning losses enabled.
- `VAD_tiny_e2e.py` and `VAD_base_e2e.py`: joint end-to-end alternative. The checked tiny e2e queue length is 3 and its total epochs is 60; inspect the exact selected config rather than assuming stage values.

The repository documentation recommends two-stage training because stage 1 can be trained once and reused for stage 2. Keep the checkpoint path valid and use matching tiny/base families.

## Plugin and data keys

A VAD config sets:

```python
plugin = True
plugin_dir = 'projects/mmdet3d_plugin/'
dataset_type = 'VADCustomNuScenesDataset'
data_root = 'data/nuscenes/'
```

The model graph starts at `model.type='VAD'`, uses a `VADHead`, and selects `VADPerceptionTransformer`. Dataset pipelines include multi-view image loading, VAD custom range/name filters, image normalization, temporal ego fields, and vector/map labels. Validation/test sections use temporal VAD PKLs and usually `nuscenes_map_anns_val.json`.

Use `--cfg-options key=value` for runtime overrides, preserving quoted list/tuple values. A config-only parse can verify inheritance and Python syntax; it cannot verify dataset files or native CUDA operators.

## Image normalization and checkpoints

The current checked configs use a newer ImageNet-style normalization (`mean=[123.675,116.28,103.53]`, standard deviations, `to_rgb=True`). The training/evaluation documentation says released checkpoint reproduction requires the legacy training setting:

```python
img_norm_cfg = dict(
    mean=[103.530, 116.280, 123.675], std=[1.0, 1.0, 1.0], to_rgb=False)
```

Use the legacy setting when reproducing released weights; otherwise metrics and visualizations can be wrong. See [training-evaluation](../../training-evaluation/SKILL.md).

## Safe inspection

Run the bundled `scripts/check_config_contract.py` with a config path. It reports model/data/plugin/queue/stage fields without importing the VAD plugin or building a model. For model roles and registered names, read [model-and-plugin-api.md](model-and-plugin-api.md).
