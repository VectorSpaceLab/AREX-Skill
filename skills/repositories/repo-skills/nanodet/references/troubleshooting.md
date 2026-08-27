# Troubleshooting

## Install and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` for `nanodet` | repo not installed, wrong environment, or editable install skipped | install the package in the target environment and re-run `python -I -c "import nanodet"` |
| `torch._six` import failure | torch 2.x installed | use a compatible `torch<2.0` / matching `torchvision` pair |
| `timm is not installed` | a config uses `TIMMWrapper` | install `timm` before loading that config |
| `pycocotools` import failure | COCO evaluator or dataset not installed | install `pycocotools` and ensure the wheel matches the Python version |
| TensorBoard import failure | logger dependency missing | install `tensorboard` |
| `onnxsim` / `onnxruntime` import failure | export stack missing optional packages | install `onnx`, `onnx-simplifier`, and `onnxruntime` |
| `cv2` import failure | OpenCV wheel missing | install `opencv-python` or `opencv-python-headless` |

## Config and data

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `cfg.model.arch.head.num_classes must equal len(cfg.class_names)` | YAML mismatch between class list and head | make the head class count match the config class list |
| `Unknown dataset type!` | unsupported dataset `name` | choose `CocoDataset`, `XMLDataset`, or `YoloDataset` |
| image path / annotation path not found | data layout mismatch | verify the dataset root and annotation paths in the config |
| `YoloDataset` skips images | a `.txt` annotation has no matching image file next to it | rename or place the image beside the annotation with a supported extension |
| `XMLDataset` drops boxes | class name missing from `class_names` or invalid box coordinates | fix the class list or annotation contents |
| `CocoDataset` rejects annotations | invalid COCO JSON, bad box dimensions, or missing categories | validate the JSON schema and box sizes |

## Training and evaluation

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| old `.pth` checkpoint warning | checkpoint uses the legacy format | convert it with the checkpoint conversion helper before reuse |
| no validation output | `save_key` missing from eval results or `val_intervals` too sparse | confirm the evaluator name and save key in the config |
| multiprocessing warnings or hangs | start method / OMP / MKL thread settings clash | use the repo's multiprocessing helper or adjust the config-provided settings |
| EMA state mismatch | model topology changed after EMA initialization | rebuild the EMA state with a matching model |
| optimizer param groups not behaving as expected | custom param-level rules or norm/bias decay are misconfigured | inspect the optimizer config and the logged special hyperparameters |

## Inference and export

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| demo tries to use CUDA on a CPU-only machine | the original demo defaults to `cuda:0` | use the skill-owned demo wrapper with explicit device selection or choose CPU inputs/configs |
| export fails on RepVGG | deploy conversion not applied | convert the model to deploy form before export |
| ONNX simplification fails | `onnxsim` / `onnxruntime` missing or incompatible | install the optional export dependencies and retry |
| FLOPs helper prints a skip message | `mobile_cv` is absent | treat it as optional and use the supported smoke checks instead |
| export shape mismatch | `input_shape` does not match the model config | keep the export input shape aligned with the training config |
| first build downloads pretrained weights | a backbone config defaults to `pretrained=True` | allow the download, cache it, or override to `pretrained=False` when offline |

## Version and compatibility notes

- The verified environment uses `torch 1.13.1+cpu` and `torchvision 0.14.1+cpu`.
- The selected CPU verification scope does not require CUDA.
- CUDA remains a documented but optional path in the repository docs.
