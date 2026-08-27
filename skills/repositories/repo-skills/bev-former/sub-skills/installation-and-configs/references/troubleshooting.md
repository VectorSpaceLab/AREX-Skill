# Troubleshooting

## Plugin import fails

Symptoms:
- `ModuleNotFoundError` for `projects.mmdet3d_plugin`
- registry entries such as `BEVFormer`, `BEVFormerV2`, `BEVFormerHead`, `PerceptionTransformer`, `BEVFormerEncoder`, `SpatialCrossAttention`, `TemporalSelfAttention`, `MSDeformableAttention3D`, `NMSFreeCoder`, `HungarianAssigner3D`, `CustomNuScenesDataset`, or `CustomNuScenesDatasetV2` are missing

Checks:
1. `plugin = True`
2. `plugin_dir = 'projects/mmdet3d_plugin/'`
3. the config is being inspected from the right repo root or with `--repo-root`
4. the plugin package exports the expected classes through its `__init__.py` files

## Config parse or pretty text fails

Symptoms:
- config loads in one environment but not another
- `pretty_text` or config serialization errors
- a `yapf`-style formatting failure

Likely cause:
- legacy OpenMMLab version skew

Fix:
- use the pinned legacy stack from the configuration notes
- avoid mixing newer `mmcv`, `mmdet`, or `mmdet3d` releases with these configs
- fall back to the static inspector when you only need a summary

## BEVFormerV2 frame mismatch

Symptoms:
- temporal shape errors
- empty history features
- a crash when the current frame or history frames do not line up

Checks:
- `frames` in the detector, transformer, and dataset agree
- `queue_length == len(frames)` for the V2 family
- the frames stay inside one scene token
- `video_test_mode` remains disabled in V2

## BEVFormer queue mismatch

Symptoms:
- history BEV is `None`
- batch shapes do not line up

Checks:
- `queue_length` in `CustomNuScenesDataset` matches the expected history stack
- `bev_size` matches `bev_h_` and `bev_w_`
- `video_test_mode` is only used with the BEVFormer family, not V2

## Missing coder or assigner dependencies

Symptoms:
- `HungarianAssigner3D` or `NMSFreeCoder` cannot build
- a matching step fails before the model runs

Checks:
- `pc_range` and `voxel_size` are present
- SciPy is available for Hungarian matching in the real runtime
- the config still points to `type='NMSFreeCoder'` and `type='HungarianAssigner3D'`

## Inspector reports unresolved bases

Symptoms:
- the script lists missing `_base_` files

Meaning:
- the config was copied without its base files, or
- you did not supply `--repo-root`

Action:
- pass `--repo-root` when the config lives in a detached tree
- or inspect the base file separately and copy the relevant values into the summary
