# UniAD repo provenance

- Schema: `disco.repo-provenance.v1`
- Repository: OpenDriveLab/UniAD
- Public project name: UniAD, "Planning-oriented Autonomous Driving"
- Remote URL: https://github.com/OpenDriveLab/UniAD.git
- Source branch: `v2.0`
- Source commit: `609ee083ea51c3521c323f1279dfc4cee0e60467`
- Exact tag: none recorded at HEAD
- Package/version metadata: no Python package distribution metadata (`setup.py`, `setup.cfg`, or `pyproject.toml`) was present; public README announces UniAD 2.0.
- Working tree state at creation: source checkout was clean before generated `skills/` outputs were added; generated `skills/` files are construction artifacts.

## Evidence paths used

- `README.md`
- `docs/INSTALL.md`
- `docs/DATA_PREP.md`
- `docs/TRAIN_EVAL.md`
- `requirements.txt`
- `docker/Dockerfile` (legacy/runtime contrast only)
- `projects/configs/_base_/datasets/nus-3d.py`
- `projects/configs/_base_/default_runtime.py`
- `projects/configs/bevformer/base_bevformer.py`
- `projects/configs/stage1_track_map/base_track_map.py`
- `projects/configs/stage2_e2e/base_e2e.py`
- `projects/mmdet3d_plugin/`
- `tools/train.py`
- `tools/test.py`
- `tools/create_data.py`
- `tools/data_converter/uniad_nuscenes_converter.py`
- `tools/analysis_tools/visualize/`
- `tools/uniad_create_data.sh`
- `tools/uniad_dist_train.sh`
- `tools/uniad_dist_eval.sh`
- `tools/uniad_slurm_train.sh`
- `tools/uniad_slurm_eval.sh`
- `tools/uniad_vis_result.sh`

## Refresh triggers

Refresh this skill when any of these change:

- UniAD moves beyond the v2.0 branch/runtime stack.
- Config paths or config defaults change, especially `load_from`, `data_root`, `queue_length`, task heads, or `plugin_dir`.
- The project adds released nuPlan/NAVSIM tools or public scripts not covered here.
- OpenMMLab/Torch/CUDA compatibility guidance changes.
- Data-preparation, evaluation, or visualization scripts change their flags or outputs.
