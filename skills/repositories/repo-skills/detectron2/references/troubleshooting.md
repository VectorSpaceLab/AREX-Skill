# Detectron2 Cross-Cutting Troubleshooting

Use this reference for installation, import, optional dependency, backend, and source-demo issues that affect multiple Detectron2 workflows. For workflow-specific failures, read the nearest sub-skill troubleshooting file.

## Install Or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'detectron2'`.
- `ModuleNotFoundError: No module named 'torch'` during Detectron2 setup.
- `ImportError: cannot import name '_C'`.
- Undefined symbols mentioning `TH`, `at::Tensor`, `torch`, `GLIBCXX`, or C++ runtime symbols.

Likely causes and fixes:

- Install a compatible `torch` and `torchvision` pair before Detectron2. Detectron2 setup imports torch and builds native extensions against the active torch ABI.
- For source builds, use a package/build process where the setup phase can import torch. If build isolation hides torch, disable build isolation after installing torch.
- If the active torch/torchvision version changed, rebuild Detectron2 and remove stale build artifacts from the package build area.
- For `_C` import errors, confirm the installed Detectron2 extension was built for the active Python, torch, CUDA, compiler, and platform.
- On old system C++ runtimes, update the runtime library or rebuild with a compatible compiler.

## CUDA And Native Extension Issues

Symptoms:

- `Not compiled with GPU support`.
- `nvcc not found`.
- `invalid device function` or `no kernel image is available for execution`.
- CUDA symbol or `libcudart.so` errors.

Likely causes and fixes:

- CPU inference can work for many models by setting `MODEL.DEVICE cpu`; training and large inference workloads usually expect GPU.
- Build CUDA extensions only when torch sees CUDA and the CUDA toolkit/compiler stack matches the torch CUDA runtime.
- Check driver/runtime/toolkit consistency with `python -m detectron2.utils.collect_env` in the runtime environment.
- For source builds on different GPU generations, set `TORCH_CUDA_ARCH_LIST` deliberately before building.
- If the host has no visible GPU or the task is CPU-only, avoid installing broad CUDA-specific extras and keep guidance CPU-focused.

## Optional Dependencies

| Dependency | Needed for | Symptom when missing | Recovery |
| --- | --- | --- | --- |
| OpenCV (`cv2`) | Demo-style image/video IO and visualization helpers | `ModuleNotFoundError: No module named 'cv2'` | Install `opencv-python` or `opencv-python-headless` for server environments. |
| Caffe2 | Optional `caffe2_tracing` export paths | `ModuleNotFoundError: No module named 'caffe2'` or missing Caffe2 exports | Prefer TorchScript unless Caffe2 runtime is required; install a torch/Caffe2 stack only if the deployment target needs it. |
| ONNX | Optional ONNX export | `ModuleNotFoundError: No module named 'onnx'` or ONNX export/runtime errors | Install ONNX only when the request explicitly targets ONNX; direct ONNX Runtime support is not guaranteed for all Detectron2 exports. |
| `pycocotools` | COCO-format datasets/evaluation | COCO helper/evaluator import errors | Install compatible `pycocotools` and validate JSON/image roots. |
| Project-specific packages | DensePose, TensorMask, ViTDet/MViTv2-style extras | Project import/config failures | Treat optional projects as opt-in; install only the dependencies required by the requested project. |

## Config And Weight Downloads

Symptoms:

- A static validation unexpectedly tries to download a model checkpoint.
- Offline environments fail while constructing `DefaultPredictor`.
- Model zoo paths resolve configs but not final trained weights.

Fix:

- For inspection, use `model_zoo.get_config_file()`, `model_zoo.get_config()`, or `model_zoo.get_checkpoint_url()`.
- Do not call `model_zoo.get(..., trained=True)`, `DefaultPredictor(cfg)`, or `DetectionCheckpointer.load()` unless loading weights is intentional.
- Set local `MODEL.WEIGHTS` or `train.init_checkpoint` when offline execution is required.
- Confirm whether the config is Yacs YAML or LazyConfig Python before choosing override syntax.

## Dataset And Metadata Symptoms

Symptoms:

- `KeyError` for an unregistered dataset name.
- Visualization has numeric labels or wrong colors.
- Evaluation reports no evaluator or wrong class counts.

Fix:

- Register datasets before building loaders, trainers, predictors that need metadata, or evaluators.
- Use `MetadataCatalog.get(name).set(...)` for class names, colors, `evaluator_type`, and COCO/LVIS/Cityscapes metadata as appropriate.
- Align `MODEL.ROI_HEADS.NUM_CLASSES`, `MODEL.RETINANET.NUM_CLASSES`, keypoint counts, semantic classes, and metadata with the custom dataset.
- Use the data-datasets validators before launching training/evaluation.

## Source Demo Caveat

The checkout used to build this skill had a demo CLI import that referenced a non-package path. Treat the original demo script as source evidence only. For future tasks, use the inference sub-skill's API patterns and bundled dry-run command builder rather than relying on the original demo file.

## When To Stop And Ask

Ask before:

- Running long training, full dataset evaluation, benchmarks, or export commands that load large checkpoints.
- Installing broad optional extras or project-specific dependency stacks.
- Mutating a user-provided Python environment.
- Downloading model weights, datasets, or external benchmark assets.
- Launching multi-GPU or multi-machine distributed jobs.
