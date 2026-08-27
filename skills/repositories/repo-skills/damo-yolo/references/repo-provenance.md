# DAMO-YOLO repo provenance

## Source identity

- Public project name: DAMO-YOLO
- Canonical generated skill id: `damo-yolo`
- Distribution/import package: `damo`
- Package version observed: `0.1.0`
- VCS: git
- Commit: `319572eef367340267ab6ab8ae253527a71d7c3a`
- Branch: `master`
- Exact tag: none observed
- Remote URL: `https://github.com/tinyvision/DAMO-YOLO.git`
- Working tree state at source evidence capture: clean before generated skill/artifact files were written. Generated paths under `skills/disco/damo-yolo/` and `skills/tests/damo-yolo/` are construction outputs, not upstream source evidence.

## Verification baseline

- Python package import verified: `import damo`, version `0.1.0`.
- Required CUDA preparation smoke verified for training/eval/model execution using CUDA-enabled PyTorch.
- CLI parser checks verified for training, evaluation, demo inference, and converter workflows.
- TensorRT/PyCUDA/pytorch-quantization runtime was not installed; TensorRT and partial INT8 flows are documented as optional/unverified backend paths.

## Source evidence paths

Relative paths used to build this skill:

- `README.md`
- `README_cn.md`
- `setup.py`
- `requirements.txt`
- `configs/*.py`
- `damo/__init__.py`
- `damo/config/base.py`
- `damo/config/paths_catalog.py`
- `damo/apis/detector_trainer.py`
- `damo/apis/detector_inference.py`
- `damo/apis/detector_inference_trt.py`
- `damo/detectors/detector.py`
- `damo/dataset/build.py`
- `damo/dataset/datasets/coco.py`
- `damo/dataset/transforms/*.py`
- `damo/base_models/backbones/*.py`
- `damo/base_models/necks/giraffe_fpn_btn.py`
- `damo/base_models/heads/zero_head.py`
- `damo/base_models/core/end2end.py`
- `damo/base_models/core/ops.py`
- `damo/utils/demo_utils.py`
- `damo/utils/model_utils.py`
- `damo/utils/boxes.py`
- `damo/utils/visualize.py`
- `damo/structures/*.py`
- `tools/train.py`
- `tools/eval.py`
- `tools/demo.py`
- `tools/converter.py`
- `tools/trt_eval.py`
- `tools/calibrator.py`
- `tools/partial_quantization/README.md`
- `tools/partial_quantization/partial_quant.py`
- `tools/partial_quantization/utils.py`
- `scripts/coco_train.sh`
- `scripts/coco_eval.sh`
- `scripts/coco_distill.sh`
- `assets/CustomDatasetTutorial.md`

## Refresh triggers

Refresh this skill if DAMO-YOLO changes any of these surfaces:

- Config class layout, TinyNAS structure file locations, or `DatasetCatalog` behavior.
- Training/eval launchers, `Trainer`, checkpoint loading, or distributed/NCCL assumptions.
- Demo inference engine dispatch, preprocessing/postprocessing, output formats, or visualization.
- Converter flags, `End2End` NMS wrappers, TensorRT export/eval scripts, or partial quantization scripts.
- Dependency metadata, package version, or Python/PyTorch compatibility.
