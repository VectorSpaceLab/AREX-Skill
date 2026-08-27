# YOLOX Repo Provenance

- Schema: `disco.repo-provenance.v1`

This generated repo skill was distilled from a YOLOX Git checkout and verified against installed-package/API evidence. It is intended as operating guidance for the versioned public package surface, not as instructions that depend on the original checkout remaining available.

## Source snapshot

- Repository: Megvii-BaseDetection/YOLOX
- Remote URL: `https://github.com/Megvii-BaseDetection/YOLOX.git`
- Commit: `6ddff4824372906469a7fae2dc3206c7aa4bbaee`
- Branch: `main`
- Exact tag: none detected at this commit
- Working tree state at creation: dirty because generated `skills/` artifacts were created in the checkout; no source-code changes were used as evidence beyond the listed repo files.
- Package/distribution name: `yolox`
- Package version: `0.3.0`

## Evidence paths

The skill was constructed from these relative repository evidence paths:

- `README.md`
- `setup.py`
- `setup.cfg`
- `requirements.txt`
- `MANIFEST.in`
- `yolox/`
- `tools/demo.py`
- `tools/train.py`
- `tools/eval.py`
- `tools/export_onnx.py`
- `tools/export_torchscript.py`
- `tools/trt.py`
- `tools/visualize_assign.py`
- `exps/default/`
- `exps/example/custom/`
- `exps/example/yolox_voc/yolox_voc_s.py`
- `docs/quick_run.md`
- `docs/train_custom_data.md`
- `docs/cache.md`
- `docs/manipulate_training_image_size.md`
- `docs/freeze_module.md`
- `docs/assignment_visualization.md`
- `docs/mlflow_integration.md`
- `docs/model_zoo.md`
- `docs/updates_note.md`
- `datasets/README.md`
- `demo/ONNXRuntime/`
- `demo/TensorRT/`
- `demo/OpenVINO/`
- `demo/ncnn/`
- `demo/MegEngine/`
- `demo/nebullvm/`
- `tests/utils/test_model_utils.py`

## Verification baseline

Private construction verification established:

- `yolox` imports and reports version `0.3.0`.
- Core/support imports passed for `torch`, `torchvision`, `cv2`, `pycocotools`, `onnx`, `onnxsim`, `onnxruntime`, `loguru`, `tqdm`, `thop`, `tabulate`, and `psutil`.
- CUDA-capable PyTorch was available during construction, and a tiny CUDA allocation passed.
- CLI help passed for demo, train, eval, ONNX export, and TorchScript export surfaces.
- Bundled generated helper scripts compile and their safe smoke/dry-run modes pass.

Do not assume a future user's runtime has the same packages, GPU, datasets, checkpoints, or optional deployment SDKs. Re-run the bundled smoke helpers in the target environment.

## Staleness triggers

Refresh this skill when:

- YOLOX package version, default experiment modules, model names, or checkpoint formats change.
- Demo, train, eval, export scripts, or deployment demos change CLI flags or behavior.
- Dataset/evaluator classes or `Exp` defaults change.
- The package switches supported PyTorch, CUDA, ONNX, or optional deployment dependency versions.
- New first-class workflows are added for serving, model zoo downloads, data conversion, or deployment backends.
