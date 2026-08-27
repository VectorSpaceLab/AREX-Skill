# Installation and Backend Notes

## Purpose

Read this before choosing which package family to inspect or which backend to verify.

## Quick baseline

| Workflow | Base install | Backend note |
| --- | --- | --- |
| Speedster inference optimization | `pip install speedster nebullvm` | Compiler/backends are optional and hardware-specific; CPU import is not enough to prove a GPU compiler path. |
| NebullVM backend support | `pip install nebullvm` | Use this for `DataManager`, `check_device`, compiler selection, and optional dependency troubleshooting. |
| Forward-Forward training | `pip install forward_forward torch torchvision` | Keep the inspection environment on Python 3.9 unless the old `collections.Generator` import is patched. |
| OpenAlphaTensor training | `pip install OpenAlphaTensor torch` | Safe inspection is config and API oriented; full training is GPU-leaning and long-running. |
| ChatLLaMA RLHF | `pip install chatllama-py` plus the runtime stack from the sub-skill reference | Full training needs DeepSpeed, Accelerate, PEFT, Transformers, datasets, and external model/data access. |

## Backend rules of thumb

- Speedster and NebullVM can be inspected on CPU, but their compiler and accelerator paths are platform-specific.
- A visible NVIDIA GPU does not imply that every compiler backend is available.
- The source docs and tests mention compiler families such as TensorRT, Torch-TensorRT, OpenVINO, ONNX Runtime, DeepSparse, TVM, BladeDISC, Intel Neural Compressor, Torch Dynamo, Torch XLA, Torch Neuron, and FasterTransformer.
- Forward-Forward is the only package in this repo that is known to be sensitive to the Python 3.10 `collections.Generator` removal.
- ChatLLaMA is the most pin-sensitive stack. If imports fail because of package-version drift, read the ChatLLaMA troubleshooting page before broad upgrades.

## What the bundled scripts should do

The bundled scripts in this skill tree only probe imports, signatures, and schemas. They should not install compilers, download datasets, or launch training.
