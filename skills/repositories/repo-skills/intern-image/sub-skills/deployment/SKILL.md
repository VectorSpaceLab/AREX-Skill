---
name: deployment
description: "Plan InternImage DCNv3, CUDA, TensorRT, and mmdeploy deployment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# InternImage deployment

Use this sub-skill when the task is about InternImage backend readiness, DCNv3 operator build diagnosis, ONNX/TensorRT export planning, mmdeploy custom operators, or CUDA/TensorRT compatibility across classification, detection, and segmentation.

Do not use this sub-skill for task-specific training, evaluation, model-family selection, dataset layout, or demo interpretation unless the blocker is deployment/backend related. Route classification model usage to the classification sub-skill, object/instance detection usage to the detection sub-skill, and semantic segmentation usage to the segmentation sub-skill.

## Fast route

1. Identify the workflow and export target:
   - `classification-onnx`: PyTorch classification checkpoint to ONNX.
   - `classification-trt`: classification ONNX plus TensorRT engine and consistency check.
   - `detection-trt`: MMDetection deployment through mmdeploy/TensorRT.
   - `segmentation-trt`: MMSegmentation deployment through mmdeploy/TensorRT.
2. Read `references/environment-matrix.md` for the minimum Python/CUDA/OpenMMLab/mmdeploy compatibility checklist.
3. Read `references/tensorrt-and-dcnv3.md` before any DCNv3 source build, prebuilt wheel choice, ONNX export, or TensorRT/mmdeploy plan.
4. Generate a safe dry-run command template with:

   ```bash
   python sub-skills/deployment/scripts/build_export_command.py --help
   python sub-skills/deployment/scripts/build_export_command.py detection-trt --model-name mask_rcnn_internimage_t_fpn_1x_coco
   ```

5. If anything fails or prerequisites are uncertain, use `references/troubleshooting.md` before recommending a build or export run.

## Operating rules

- Treat export/build commands as explicit user-approved actions. The bundled script only prints templates; it never downloads, builds, imports OpenMMLab, or launches TensorRT.
- Distinguish a CUDA runtime that PyTorch can use from the CUDA toolkit/nvcc needed by DCNv3 and mmdeploy custom-op compilation.
- Do not claim TensorRT/mmdeploy verification unless the environment has TensorRT, CUDNN, mmdeploy, a compatible PyTorch CUDA wheel, compiled DCNv3, and the mmdeploy TensorRT backend op for `mmdeploy::TRTDCNv3`.
- Prefer a matching prebuilt DCNv3 wheel when available for the target PyTorch/CUDA combination; use source build only when nvcc/toolkit and ABI compatibility are explicit.
- Keep deployment plans placeholder-safe: use `<INTERNIMAGE_REPO>`, `<checkpoint.pth>`, `<MMDEPLOY_DIR>`, `<TENSORRT_DIR>`, and `<CUDNN_DIR>` until the user provides concrete paths.

## Bundled materials

- `references/tensorrt-and-dcnv3.md` - DCNv3 operator surfaces, mmdeploy/TensorRT custom-op build sequence, source-script decisions, and export command semantics.
- `references/environment-matrix.md` - compatibility matrix for CPU guidance, CUDA runtime/toolkit, OpenMMLab pins, mmdeploy/TensorRT, and current verification limits.
- `references/troubleshooting.md` - failure-mode triage for missing nvcc, `Cuda is not availabel`, missing custom ops, import/version conflicts, ONNX/TensorRT errors, and export input mistakes.
- `scripts/build_export_command.py` - standalone dry-run command builder for classification ONNX, classification TensorRT, detection TensorRT, and segmentation TensorRT.
