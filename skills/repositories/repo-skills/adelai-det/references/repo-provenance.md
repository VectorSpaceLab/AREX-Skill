# AdelaiDet repo provenance

Schema: `disco.repo-provenance.v1`

Generated skill id: `adelai-det`

Generation timestamp (UTC): 2026-08-16T19:27:50Z

## Source snapshot

- Repository: AdelaiDet
- Branch observed: `master`
- Commit: `5e19cb172b8363820b409ed1a2754fb19ad3acb8`
- Exact tag: none observed
- Source distribution name: `AdelaiDet`
- Python import root: `adet`
- `setup.py` package version: `0.2.0`
- `adet.__version__`: `0.1.1`

## Working tree state at generation

The source tree was otherwise the checked-out repository plus newly generated production artifacts under `skills/`. The generated `skills/` files were untracked and should not be treated as upstream AdelaiDet source evidence.

## Evidence used

Primary evidence paths, all relative to the AdelaiDet source root:

- `README.md`
- `MODEL_ZOO.md`
- `setup.py`
- `docker/Dockerfile`
- `docs/modules/*.rst`
- `adet/__init__.py`
- `adet/config/config.py`
- `adet/config/defaults.py`
- `adet/data/**`
- `adet/evaluation/**`
- `adet/layers/**`
- `adet/modeling/**`
- `adet/structures/**`
- `adet/utils/visualizer.py`
- `configs/*/README.md`
- `configs/**/*.yaml`
- `datasets/README.md`
- `datasets/*.py`
- `demo/demo.py`
- `demo/predictor.py`
- `tools/train_net.py`
- `tools/visualize_data.py`
- `tools/convert_fcos_weight.py`
- `tools/rename_blendmask.py`
- `tools/remove_optim_from_ckpt.py`
- `onnx/README.md`
- `onnx/export_model_to_onnx.py`
- `onnx/test_onnxruntime.py`
- `onnx/pytorch-onnx-caffe-ncnn*.sh`

## Verification baseline

Runtime validation used a CUDA-capable legacy stack because unmodified AdelaiDet CUDA sources include PyTorch THC headers that are absent from modern PyTorch 2.x.

Verified capabilities:

- Package import: `import adet`
- Config API: `adet.config.get_cfg()` with FCOS, BAText, BlendMask, CondInst, SOLOV2, and FCPose sections
- Detectron2 registration: AdelaiDet meta-architectures/backbones/ROI heads registered after `import adet.modeling`
- Compiled extension: `adet._C` with `bezier_align_*`, `def_roi_align_*`, and `ml_nms`
- Tiny CUDA BezierAlign forward
- Tiny CUDA DefROIAlign forward
- Tiny CUDA multi-label NMS
- CLI help for training, demo inference, dataset visualization, and ONNX export

Review artifacts from generation are not runtime skill dependencies and are intentionally not linked from this public skill tree.

## Refresh guidance

Refresh this skill when any of the following changes:

- AdelaiDet source commit, especially `setup.py`, `adet/layers/csrc`, `adet/config/defaults.py`, `adet/modeling`, `tools/train_net.py`, `demo/demo.py`, `datasets/`, or `onnx/`.
- Detectron2 API compatibility, PyTorch/CUDA compatibility, or the build outcome for `adet._C`.
- New config families, renamed config keys, changed model zoo links, or updated dataset layouts.
- New public CLIs, demos, conversion scripts, deployment targets, or documented evaluation protocols.

On refresh, rerun `scripts/check_install.py --cuda-ops` and update this provenance file plus `references/repo-routing-metadata.json` if scenario coverage changes.
