# Jittor package map

This is the short route map for public modules. Use the sub-skills for the workflow details.

| Public surface | Typical task family | Owning sub-skill |
| --- | --- | --- |
| `jittor` root module | Vars, gradients, execution, `Module`, `Function`, save/load, sync, no-grad scopes | `core-api-and-autograd` |
| `jittor.nn` | Layers, losses, activations, optimizers, schedulers, training loops | `nn-training-workflows` |
| `jittor.optim` | Optimizer classes and learning-rate scheduler helpers | `nn-training-workflows` |
| `jittor.dataset` | Dataset and dataloader setup, built-in datasets, worker behavior | `datasets-models-and-io` |
| `jittor.transform` | Image preprocessing and augmentation | `datasets-models-and-io` |
| `jittor.models` | Built-in model zoo constructors and pretrained loading | `datasets-models-and-io` |
| `jittor_utils.config` | C++ console flag generation and compile command templates | `custom-op-console-and-tools` |
| `jittor_utils.clean_cache` | Cache inspection and cleanup categories | `runtime-and-installation` |
| `jt.code`, `compile_custom_op(s)` | Custom operators and inline kernels | `custom-op-console-and-tools` |

## Simple routing rule

- If the user mentions tensors, gradients, or `Module.execute`, go to `core-api-and-autograd`.
- If the user mentions a model, optimizer, scheduler, or training loop, go to `nn-training-workflows`.
- If the user mentions data loading, transforms, or a model-zoo backbone, go to `datasets-models-and-io`.
- If the user mentions compiler flags, `nvcc_path`, cache cleanup, CUDA/ROCm/MPI, or timing, go to `runtime-and-installation`.
- If the user mentions custom ops, `jt.code`, C++ console embedding, or utility CLIs, go to `custom-op-console-and-tools`.

## Notes

- The package is designed around lazy execution. Use synchronized reads only when you need a concrete value.
- Optional hardware backends are not implied by the package name alone; treat them as separate capabilities.