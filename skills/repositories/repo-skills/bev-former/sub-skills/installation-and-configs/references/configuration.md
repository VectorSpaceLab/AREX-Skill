# Configuration notes

This sub-skill covers the legacy OpenMMLab stack used by BEVFormer. The source install notes pin a narrow dependency set:
- PyTorch 1.9.1 + cu111, torchvision 0.10.1 + cu111, torchaudio 0.9.1
- mmcv-full 1.4.0
- mmdet 2.14.0
- mmsegmentation 0.14.1
- mmdet3d 0.17.1
- Detectron2 and the supporting utility packages named in the source docs

If config parsing or plugin import fails, treat the stack as version-skewed before blaming the config. See [Troubleshooting](troubleshooting.md).

## Inheritance pattern

- BEVFormer configs usually inherit `../datasets/custom_nus-3d.py` and `../_base_/default_runtime.py`.
- BEVFormerV2 configs usually inherit only `../_base_/default_runtime.py`.
- `plugin = True` and `plugin_dir = 'projects/mmdet3d_plugin/'` are required for the custom registries.
- `plugin_dir` stays a repo-relative path in the generated configs; the inspector can still summarize it without importing the original checkout.

## Family map

| Config | Family | What it changes | Why it is useful |
| --- | --- | --- | --- |
| `projects/configs/bevformer/bevformer_tiny.py` | BEVFormer | R50 backbone, 50x50 BEV grid, 3-frame queue, single-scale C5 features | Fastest plugin and config smoke target |
| `projects/configs/bevformer/bevformer_small.py` | BEVFormer | R101-DCN backbone, 150x150 BEV grid, 3-frame queue | Smaller than base but still representative |
| `projects/configs/bevformer/bevformer_base.py` | BEVFormer | Full 200x200 BEV grid and 4-frame queue | Main BEVFormer baseline |
| `projects/configs/bevformerv2/bevformerv2-r50-t1-base-24ep.py` | BEVFormerV2 | Single-frame V2 path with DD3D supervision | Best V2 import and config smoke target |
| `projects/configs/bevformerv2/bevformerv2-r50-t2-48ep.py` | BEVFormerV2 | Two-frame temporal queue via `frames` | Check temporal frame wiring |
| `projects/configs/bevformerv2/bevformerv2-r50-t8-24ep.py` | BEVFormerV2 | Eight-frame temporal queue and Group-DETR head | Check the widest temporal config |

## Knobs that must stay aligned

- `point_cloud_range` and `voxel_size` are paired.
- `bev_h_` and `bev_w_` must match `pts_bbox_head.bev_h`, `pts_bbox_head.bev_w`, and the positional encoding row and column embeds.
- `queue_length` belongs to `CustomNuScenesDataset`.
- `frames` belongs to `CustomNuScenesDatasetV2` and to the V2 detector and transformer path.
- `frames` length must match the temporal queue expected by the V2 family.
- `use_grid_mask`, `video_test_mode`, `num_levels`, `num_mono_levels`, `mono_loss_weight`, and `group_detr` are model-family knobs, not dataset-layout knobs.
- `BEVFormerV2` keeps `video_test_mode = False` in the current code path.
- The V2 family adds a mono/DD3D branch, so the extra Detectron2-related install notes matter there.

## Static inspection helper

Use [scripts/inspect_bevformer_config.py](../scripts/inspect_bevformer_config.py) for a read-only summary of:
- base files and inheritance order;
- plugin settings;
- model family, head family, and backbone choice;
- BEV grid size and temporal queue or frame wiring;
- dataset family and key schedule fields.

The inspector is static: it does not import `mmcv`, `mmdet`, `mmdet3d`, or the plugin. Missing base files are reported as warnings instead of requiring the original checkout.
