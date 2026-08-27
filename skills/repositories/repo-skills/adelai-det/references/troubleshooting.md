# AdelaiDet troubleshooting

Start with `setup-build` for install/import/build errors. Start with the workflow-specific sub-skill for config, data, demo, training, or export errors.

## Install/build errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` during `pip install -e .` | Pip build isolation hides the already installed PyTorch package while `setup.py` imports torch. | Use `python -m pip install --no-build-isolation -e .` after installing PyTorch. |
| `fatal error: THC/THC.h: No such file or directory` | PyTorch 2.x removed THC headers used by AdelaiDet `ml_nms.cu`. | Use PyTorch 1.10.x + CUDA 11.3 for unmodified source, or intentionally patch the native extension. |
| `cuda_runtime.h: No such file or directory` | NVCC is present but CUDA development headers are missing. | Install the matching CUDA toolkit development package, e.g. `cudatoolkit-dev=11.3.1` for the verified stack. |
| `PIL.Image has no attribute LINEAR` | Detectron2 0.6 is incompatible with Pillow 10+. | Pin `Pillow<10`. |
| `cannot import name 'string_metric' from rapidfuzz` | AdelaiDet text evaluator expects rapidfuzz 2.x API. | Pin `rapidfuzz<3`. |
| `No module named cv2` | OpenCV is not installed but SOLOv2/demo/data utilities import it. | Install `opencv-python-headless==4.8.1.78` with NumPy 1.23.x for the verified stack. |
| CUDA build works but CUDA smoke fails | Architecture mismatch or runtime library issue. | Set `TORCH_CUDA_ARCH_LIST` for the target GPU, rebuild cleanly, and rerun `scripts/check_install.py --cuda-ops`. |

## Import/config errors

- Always create configs with `adet.config.get_cfg()` or call `add_adet_config(cfg)` before merging YAML.
- If a config says a meta-architecture/backbone/head is missing, first verify that `import adet` succeeds; `adet/__init__.py` imports modeling modules to register objects.
- If a YAML key does not exist, check whether the file belongs to the matching model family. FCOS, BAText, BlendMask, CondInst, SOLOv2, MEInst, and FCPose do not share every key.

## Dataset errors

- Use `data-prep` before training when the error names missing annotation JSON, text lexicon files, `thing_train2017`, MEInst components, or dataset registration.
- Built-in dataset registration assumes conventional relative dataset folders and filenames. For custom datasets, either register them in a small launcher or override config dataset names to already-registered datasets.
- Text spotting requires Bezier/control-point annotations and evaluator-specific dictionaries/lexicons. A COCO box-only dataset is not enough for BAText recognition.

## Training/evaluation errors

- Run `sub-skills/train-eval/scripts/run_train_eval.py --dry-run ...` first to inspect the exact command and paths.
- `--eval-only` still needs a valid config, model weights, and registered datasets.
- Distributed runs use Detectron2 launch arguments (`--num-gpus`, `--num-machines`, `--machine-rank`, `--dist-url`). Keep config batch sizes consistent with the actual GPU count.
- If a model loads but state-dict keys mismatch, use `export-convert` checkpoint utilities or inspect whether the checkpoint is from official FCOS/BlendMask naming conventions.

## Demo/visualization errors

- Demos need `MODEL.WEIGHTS`, a config, and one of image input, video input, or webcam.
- Output behavior differs by mode: image outputs can be a directory or file; video outputs require codec support; webcam mode opens a display/window and is unsuitable on headless machines.
- For text models, route to `text-spotting` if output boxes/recognized strings are missing or lexicon-dependent.

## Export/deployment errors

- ONNX export is only a first step. Runtime comparison with Caffe2, ONNXRuntime, TensorRT, Caffe, or NCNN needs extra packages/projects and model artifacts.
- Source shell scripts for Caffe/NCNN conversion assume external absolute workspaces. Do not run them unreviewed; use `export-convert` references to reconstruct a safe local pipeline.
- Exported models may be limited to FCOS/BlendMask/CondInst-style heads supported by the source ONNX script.
