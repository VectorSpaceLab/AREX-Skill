# Install and environment troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: megatron` or `megatron.core` | Wrong Python, package not installed, or command launched outside the intended environment. | Run `python -m pip show megatron-core`; run the bundled environment probe with the same `python` that will launch training. |
| `pip show megatron-core` works but import fails | Broken editable install, incompatible Python, missing base dependency, or import-time optional package error. | Run `python -m pip check`; reinstall only the needed package/extras; inspect the first traceback frame rather than later warnings. |
| CUDA GPUs visible in `nvidia-smi` but `torch.cuda.is_available()` is false | CPU-only Torch wheel, driver/wheel mismatch, container did not receive GPUs, or `CUDA_VISIBLE_DEVICES` hides devices. | Print `torch.__version__` and `torch.version.cuda`; verify container flags; install a CUDA Torch build compatible with the driver. |
| `no kernel image is available` | Installed binary does not support the GPU compute capability. | Choose a newer Torch/CUDA wheel or a container that supports the GPU generation. |
| TransformerEngine/Apex warnings on import | Minimal environment lacks optional acceleration packages. Many local/Torch fallback paths still import. | If the workflow needs FP8/FP4/TE layer specs or fused multi-tensor kernels, install a compatible TE/Apex path or use the supported container; otherwise record the fallback. |
| `nvidia-modelopt` import failure | ModelOpt post-training dependencies were not installed. | Route to the post-training workflow and install ModelOpt only for that selected task. |
| Editable build killed or OOM | Too many parallel compiler jobs or broad extras compiling CUDA extensions. | Set `MAX_JOBS=4` or lower; prefer the NGC/container path for full dev/TE/Mamba/ModelOpt. |
| `uv sync --locked` or dependency resolution fails | Wrong environment (host instead of container), stale lock, or changed dependency set. | For repo maintenance, use the CI container and route to `testing-ci-and-maintenance`; do not hand-edit `uv.lock`. |
| FP8 example fails on A100 | FP8 recipes target Hopper/Ada/Blackwell-style support; A100 is not equivalent. | Do not claim FP8 validation on A100. Use BF16/FP16 or move to supported hardware. |
| NCCL/runtime error after environment passes import | Environment probe only proved Torch/CUDA import and tiny allocation. | Route to training/inference troubleshooting; scan first Python traceback across ranks and verify launch topology. |

## What not to do

- Do not install every optional group just because a workflow is unclear.
- Do not count CPU importability as proof of CUDA training or inference.
- Do not mutate a user-managed Conda/base environment to repair Megatron-LM unless the user explicitly approves.
- Do not silence safe optional-dependency warnings by installing mismatched CUDA extension wheels.
