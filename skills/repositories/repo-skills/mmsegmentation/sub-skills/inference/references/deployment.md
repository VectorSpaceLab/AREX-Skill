# Deployment Notes

This sub-skill primarily covers PyTorch/MMEngine inference inside MMSegmentation. Switch to deployment tooling when the user needs ONNX Runtime, TensorRT, NCNN, OpenVINO, CoreML, an SDK package, or production-serving artifacts.

## When PyTorch inference is enough

Use `MMSegInferencer` or `init_model` + `inference_model` when:

- The user has a MMSegmentation config and PyTorch checkpoint.
- The task is local validation, visualization, mask export, smoke testing, or small batch inference.
- The user needs `SegDataSample`, logits/depth structures, or Python customization.
- The target environment can install compatible `torch`, `mmengine`, `mmcv`, and `mmsegmentation` packages.

## When MMDeploy is the right path

Use MMDeploy or a deployment-specific skill/path when:

- The user requests ONNX, TensorRT, OpenVINO, NCNN, PPLNN, CoreML, or SDK runtime inference.
- The user needs a portable model package with `deploy.json`, `detail.json`, `pipeline.json`, and backend model files.
- The user needs dynamic/static shape conversion, fp16/int8 precision, or backend-specific acceleration.
- The inference environment cannot carry the full PyTorch/MMSegmentation stack.

## Conversion shape and backend caveats

MMSegmentation deployment config names follow the backend/precision/shape pattern used by MMDeploy, such as `segmentation_onnxruntime_dynamic.py` or `segmentation_tensorrt-fp16_dynamic-512x1024-2048x2048.py`.

Key caveats:

- TensorRT conversion should use a CUDA device.
- Some architectures require static-shape deployment configs because backend operators may not support dynamic adaptive pooling.
- MMSegmentation deployment notes state that mmseg models support whole inference mode in deployment.
- To export probabilistic feature maps instead of argmax labels, deployment configs may need `codebase_config = dict(with_argmax=False)`.

## Runtime inference distinction

PyTorch MMSegmentation inference:

```python
from mmseg.apis import init_model, inference_model
model = init_model(model_cfg, checkpoint, device='cpu')
result = inference_model(model, image)
```

MMDeploy backend inference builds a task processor and backend model from deploy/model configs, then runs `model.test_step` on deployment-preprocessed inputs.

MMDeploy SDK inference uses `mmdeploy_runtime.Segmentor(model_path=..., device_name='cpu', device_id=0)` and returns a segmentation map directly from an image array.

Do not mix these APIs in the same code path unless the user explicitly asks to compare PyTorch and deployed outputs.
