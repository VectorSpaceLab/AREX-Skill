# Cross-Cutting Troubleshooting

Start here when the symptom is broad or appears before a specific compile/runtime/deployment sub-skill can be selected.

## Quick triage order

1. **Import and version**: verify `torch`, `torch_tensorrt`, and TensorRT package versions from the same Python environment.
2. **Feature gates**: print `torch_tensorrt.ENABLED_FEATURES` and decide whether the requested workflow is actually enabled.
3. **CUDA visibility**: run a tiny PyTorch CUDA allocation and `torch.cuda.synchronize()` before compiling.
4. **Minimal compile**: for compiler issues, test a tiny CUDA `nn.Module` with `ir='dynamo'` and static shapes before moving to the user's model.
5. **Model-specific analysis**: use `dryrun`, `Debugger`, `torch_executed_ops`, or a smaller `min_block_size` to identify unsupported ops and partitioning behavior.
6. **Artifact target**: confirm whether the user needs `.ep`, `.ts`, `.pt2`, `.engine`, Triton, C++, ExecuTorch, or distributed runtime; different targets have different prerequisites.

## Error patterns

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| `No module named torch_tensorrt` | Wrong Python environment or package missing. | Use the root environment probe and install the matching package flavor. |
| `No module named tensorrt` | TensorRT package missing for the selected standard workflow. | Install `tensorrt` compatible with the user's CUDA/PyTorch stack, or intentionally switch to TensorRT-RTX when appropriate. |
| `torch-tensorrt requires torch...` in `pip check` | Version mismatch between PyTorch and Torch-TensorRT. | Align stable/nightly package indexes; do not ignore this for production. |
| `CUDA-capable device(s) is/are busy or unavailable` | GPU is busy, hidden, exclusive, or blocked by scheduler/MIG. | Set `CUDA_VISIBLE_DEVICES` to an idle GPU, test PyTorch CUDA alone, then retry. |
| `Torch-TensorRT Runtime is not available` | Python-only or no-runtime build. | Use `.ep` Python runtime workflows or reinstall/build with runtime libraries. |
| `TorchScript Frontend is not available` | No TorchScript frontend in the installed wheel/build. | Prefer Dynamo unless the user explicitly needs TorchScript/C++; otherwise rebuild with TorchScript enabled. |
| `TensorRT-RTX is not available` | Standard TensorRT package installed while RTX-only runtime settings were requested. | Install/use `torch-tensorrt-rtx` and verify `ENABLED_FEATURES.tensorrt_rtx`. |
| QDP plugin unavailable | TensorRT plugin package missing, TensorRT version bug, TensorRT-RTX variant, or missing CUDA Python/core deps. | Route to extensibility/debugging and verify QDP prerequisites before writing kernel code. |
| Quantization import warnings | ModelOpt optional dependency absent. | Install ModelOpt only for quantization workflows and verify Python-version compatibility. |
| Engine serialization or load fails | Artifact/runtime mismatch, Python-only build limitation, dynamic-shape runtime cache issue, or unavailable C++ runtime. | Check artifact matrix and reproduce with a tiny static-shape model before blaming the user's model. |
| Performance worse than eager | No warmup, wrong opt shape, unsupported-op fallback, tiny model overhead, dynamic shape recompilation/cache issue, or CPU timing mistake. | Use runtime optimization benchmarking guidance with CUDA events and compare partitioning. |
| Unsupported op or converter failure | Op not covered by TensorRT converter, data-dependent op, shape issue, or unsupported dtype/layout. | Use `dryrun`, fallback controls, model rewrite, or custom converter/plugin decision tree. |

## Safe minimal compile check

Use this only after import and CUDA checks pass. It should finish quickly on a working GPU stack, but it still compiles a TensorRT engine.

```python
import torch
import torch_tensorrt

class Tiny(torch.nn.Module):
    def forward(self, x):
        return torch.relu(x + 1)

model = Tiny().eval().cuda()
inputs = [torch.randn(1, 4, device='cuda')]
compiled = torch_tensorrt.compile(model, ir='dynamo', inputs=inputs, enabled_precisions={torch.float32})
torch.testing.assert_close(compiled(*inputs), model(*inputs), rtol=1e-4, atol=1e-4)
```

If this fails, focus on environment/backend problems before investigating a large user model. If this passes but the user model fails, switch to the compilation/debugging sub-skills.

## Do not overclaim

- A successful import does not prove TensorRT engine build, serialization, Triton serving, C++ runtime, distributed collectives, QDP kernels, or quantization.
- A successful compile of one static toy model does not prove all dynamic-shape or production-shape profiles.
- Synthetic guidance can validate instructions, but accelerator runtime claims require runtime evidence on the target backend.
