# Repo Provenance

Schema: `disco.repo-provenance.v1`

- Skill id: `yolov7-d2`
- Source repository: YOLOv7-d2, a Detectron2-based object detection and instance segmentation project.
- Public remote observed in checkout: `https://github.com/lucasjinreal/yolov7_d2.git`
- Package metadata URL: `https://github.com/jinfagang/yolov7_d2`
- Git commit: `780512971dec4f64a66e23bd304f127a19dd842a`
- Branch: `main`
- Exact tag: none observed
- Working tree state during distillation: clean
- Distribution name: `yolov7_d2`
- Import package: `yolov7`
- Package version: `0.0.3`

## Evidence paths used

- `setup.py`
- `requirements.txt`
- `yolov7/version.py`
- `readme.md`
- `docs/install.md`
- `docs/usage.md`
- `yolov7/config.py`
- `yolov7/data/`
- `yolov7/modeling/`
- `yolov7/evaluation/coco_evaluation.py`
- `yolov7/optimizer/`
- `configs/`
- `train_det.py`
- `train_inseg.py`
- `train_transformer.py`
- `train_custom_datasets.py`
- `tools/train_detr.py`
- `tools/lazyconfig_train_net.py`
- `demo.py`
- `demo_lazyconfig.py`
- `tools/benchmark.py`
- `tools/eval_coco.py`
- `tools/compute_anchors.py`
- `tools/convert_detr_to_d2.py`
- `tools/convert_anchordetr_to_d2.py`
- `tools/convert_smcadetr_to_d2.py`
- `export.py`
- `deploy/ort_infer.py`
- `deploy/demo_quantized_int8.py`
- `deploy/quant_onnx/readme.md`
- `deploy/trt_cc/readme.md`

## Staleness triggers

Refresh this skill if the repository changes `yolov7/config.py`, training/demo/export scripts, `yolov7/data/`, `yolov7/modeling/`, `configs/`, dependency metadata, or Detectron2/PyTorch compatibility guidance. Refresh immediately if `demo_lazyconfig.py` no longer has the documented `q` runtime bug or if new console entry points replace the root scripts.
