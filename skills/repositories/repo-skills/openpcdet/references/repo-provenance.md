# OpenPCDet Repo Provenance

Schema: `disco.repo-provenance.v1`

## Source identity

- Repository: OpenPCDet
- Branch at construction: `master`
- Commit at construction: `233f849829b6ac19afb8af8837a0246890908755`
- Package version observed after editable build: `0.6.0+233f849`
- Dirty state at construction: generated `skills/` output was untracked; no source-code edits were made for this skill.

## Runtime facts verified during construction

- Python import package: `pcdet`
- PyTorch observed: `2.6.0+cu124`, compiled for CUDA `12.4`
- CUDA hardware observed: CUDA available with A100-class GPUs
- spconv/cumm observed: `spconv-cu124 2.3.8`, `cumm-cu124 0.7.11`
- OpenPCDet native CUDA extension imports observed:
  - `pcdet.ops.iou3d_nms.iou3d_nms_cuda`
  - `pcdet.ops.roiaware_pool3d.roiaware_pool3d_cuda`
  - `pcdet.ops.roipoint_pool3d.roipoint_pool3d_cuda`
  - `pcdet.ops.pointnet2.pointnet2_stack.pointnet2_stack_cuda`
  - `pcdet.ops.pointnet2.pointnet2_batch.pointnet2_batch_cuda`
  - `pcdet.ops.bev_pool.bev_pool_ext`
  - `pcdet.ops.ingroup_inds.ingroup_inds_cuda`
- `pcdet.datasets` import required `kornia==0.6.12` in the construction environment; newer kornia builds triggered an Argo2 TorchScript shape-inference error with the observed PyTorch version.

## Evidence paths used

Repository evidence was distilled from these relative paths:

- `README.md`
- `setup.py`
- `requirements.txt`
- `docker/README.md`
- `docs/INSTALL.md`
- `docs/GETTING_STARTED.md`
- `docs/DEMO.md`
- `docs/CUSTOM_DATASET_TUTORIAL.md`
- `docs/changelog.md`
- `docs/guidelines_of_approaches/bevfusion.md`
- `docs/guidelines_of_approaches/mppnet.md`
- `pcdet/config.py`
- `pcdet/datasets/__init__.py`
- `pcdet/datasets/*/*_dataset.py`
- `pcdet/models/__init__.py`
- `pcdet/models/detectors/__init__.py`
- `pcdet/models/detectors/*.py`
- `pcdet/models/backbones_*`, `pcdet/models/dense_heads`, `pcdet/models/roi_heads`
- `pcdet/ops/**`
- `pcdet/utils/spconv_utils.py`
- `tools/train.py`
- `tools/test.py`
- `tools/demo.py`
- `tools/eval_utils/eval_utils.py`
- `tools/process_tools/create_integrated_database.py`
- `tools/scripts/*.sh`
- `tools/cfgs/**/*.yaml`

## Staleness checks for future agents

Reload or refresh this skill when any of these change:

- `setup.py`, `requirements.txt`, native extension sources under `pcdet/ops/`, or spconv compatibility utilities.
- CLI signatures in `tools/train.py`, `tools/test.py`, `tools/demo.py`, or dataset `__main__` blocks.
- Dataset config schemas under `tools/cfgs/dataset_configs/`.
- Model registry entries in `pcdet/models/detectors/__init__.py` or config YAMLs under `tools/cfgs/*_models/`.
