# Cross-cutting troubleshooting

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: mmcv` or `ModuleNotFoundError: torch` | Base CV stack is missing | Install the package into a compatible PyTorch / mmcv environment first. |
| `ModuleNotFoundError: easy_predict` | Batch prediction extra is missing | Install `easy_predict` before using `easycv.tools.predict`. |
| `ModuleNotFoundError: modelscope` | ModelScope plugin is missing | Install `modelscope` only if you need the ModelScope integration. |
| `ImportError` from `blade_compression`, `pai_nni`, `onnxruntime`, or `torch_blade` | Optional optimization dependency is missing | Install only the extra needed by the selected optimization path. |

## Config and model-selection failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `model_type must be in [...]` | Template key is not one of the supported `CONFIG_TEMPLATE_ZOO` keys | Use a key from the model-zoo reference or pass an explicit config path. |
| `config file will be replaced by ...` surprises you | `--model_type` is overriding the path you passed | Remove `--model_type` when you want to use a concrete config file. |
| Missing `eval_pipelines` during training | The config was copied from a training-only example | Add a validation pipeline or choose a config that already defines evaluation. |

## Backend and hardware failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `fp16 can only be used in gpu` | The command is running on CPU | Switch to a CUDA-capable environment or drop `--fp16`. |
| TorchAccelerator tutorial fails on the host | Missing CUDA 11.3-compatible runtime or TorchAcc setup | Use the documented container or install the required backend stack. |
| Blade export fails early | Blade runtime or `torch_blade` is not present | Install the Blade dependencies for the export path or stay on raw / JIT export. |
| DALI-backed dataloaders fail to import | `nvidia-dali` is missing | Install the DALI wheel or switch to a non-DALI config. |

## Data and OSS failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| OSS reads / writes fail | OSS credentials or config not loaded | Configure `easycv.file.io.access_oss(...)` or the documented OSS config file. |
| Batch prediction on URLs fails | The input file / table schema does not match the predictor expectation | Re-read the batch prediction reference and fix the file or table schema. |
| Exported JIT / Blade inference fails to load | Sidecar config files or preprocess artifacts are missing | Keep the exported model, config JSON, and preprocess artifact together. |

## Distributed launch failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Training hangs on launch | Port conflict or bad launcher choice | Change the port, confirm `LOCAL_RANK`, and use the launcher variant that matches the job scheduler. |
| Results differ between ranks | Seed or deterministic settings are not aligned | Set `--seed` and review `--diff-seed` / `--deterministic`. |

