# Backend build and import contract

TurboDiffusion's acceleration path combines Python packages, a compiled CUDA extension, Triton kernels, and optional SageSLA dependencies. Backend-only validation should never download model weights or execute generation.

## Components

| Component | Role | Required for |
| --- | --- | --- |
| CUDA-capable PyTorch | Tensor allocation, model execution, extension ABI | Full TurboDiffusion inference and custom-op smoke checks |
| Triton | FastNorm kernels and SLA attention kernels | FastRMSNorm/FastLayerNorm, SLA |
| `flash-attn` | Wan/rCM network import path and training utilities | Parser/model imports that touch Wan network modules |
| `turbo_diffusion_ops` | Compiled CUDA extension exposing quantization and GEMM kernels | `Int8Linear`, `int8_quant`, quantized checkpoints |
| CUTLASS headers | Included by the custom extension build | Source/editable builds of `turbo_diffusion_ops` |
| CUDA toolkit developer files | `nvcc`, CUDA headers, and CUDA libraries for extension compilation | Source/editable builds |
| SpargeAttn (`spas_sage_attn`) | Optional SageAttention-backed sparse-linear attention kernels | `attention_type=sagesla` |

## Public install and source-build patterns

Use the public package install when possible:

```bash
pip install turbodiffusion --no-build-isolation
```

For a source checkout, initialize submodules before the editable build so CUTLASS headers are present:

```bash
git submodule update --init --recursive
pip install -e . --no-build-isolation
```

SageSLA is not enabled by the base package alone. Install SpargeAttn only when the user explicitly wants `attention_type=sagesla` and accepts the additional source-build dependency:

```bash
pip install git+https://github.com/thu-ml/SpargeAttn.git --no-build-isolation
```

These commands are generic package operations. Do not embed private environment prefixes, local checkout paths, credentials, or model-weight downloads in runtime instructions.

## Extension metadata distilled from the build

The package build defines one CUDA extension named `turbo_diffusion_ops`. It compiles bindings and kernels from the TurboDiffusion ops tree:

- C++ binding: `bindings.cpp`
- Quantization kernel: `quant.cu`
- Norm kernels: `rmsnorm.cu`, `layernorm.cu`
- INT8 GEMM kernel: `gemm.cu`

The extension uses C++17/NVCC flags including optimized compilation, relaxed constexpr/lambda support, fast math, `EXECMODE=0`, and generated code targets for recent NVIDIA architectures including SM80, SM89, SM90, SM100, and SM120a. The source distribution manifest includes `.cu`, `.h`, `.cuh`, `.cpp`, `.hpp`, and `.py` files under the ops package so source builds have the kernel sources available.

The build includes CUTLASS headers from the ops submodule and links against CUDA. Editable or source installs therefore need all of the following to be visible to the build backend:

1. CUDA-capable PyTorch matching the target CUDA runtime.
2. A CUDA toolkit with `nvcc` and developer headers/libraries, not just a runtime driver.
3. Initialized CUTLASS submodule contents.
4. Enough build resources; reduce parallel jobs if compilation is killed by memory pressure.

## Minimal backend smoke checks

Run the bundled diagnostic before running inference or checkpoint conversion:

```bash
python sub-skills/acceleration-backends/scripts/check_acceleration_backend.py
```

For workflows that require the custom CUDA kernels, fail fast when CUDA is unavailable:

```bash
python sub-skills/acceleration-backends/scripts/check_acceleration_backend.py --require-cuda
```

For `attention_type=sagesla`, also require the optional SpargeAttn signal:

```bash
python sub-skills/acceleration-backends/scripts/check_acceleration_backend.py --require-cuda --require-sagesla
```

Expected strong signals are:

- `torch` imports and reports the intended CUDA runtime.
- `torch.cuda.is_available()` is true for CUDA-required workflows.
- `turbo_diffusion_ops` imports and exposes quant/GEMM symbols.
- `turbodiffusion.ops` imports and tiny INT8/FastNorm CUDA checks pass when CUDA is available.
- `turbodiffusion.SLA.core` imports and reports whether `SAGESLA_ENABLED` is true.

Missing SpargeAttn is not a failure for `attention_type=sla` or `original`; it is a failure for `sagesla`.

## Source-layout import quirk

Several repository scripts were authored for a source layout and import top-level modules such as `imaginaire`, `rcm`, `ops`, `SLA`, `serve`, or `modify_model`. When running those public scripts from source, prepend the package's inner source directory to `PYTHONPATH` generically, for example:

```bash
PYTHONPATH=<path-to-inner-turbodiffusion-directory> python <script-or-module> --help
```

Do not hard-code a machine-specific checkout path. Installed package APIs should prefer fully qualified imports such as `turbodiffusion.ops` and `turbodiffusion.SLA` where available; source-authored scripts may still require the top-level import layout.

## Backend-only validation boundary

Backend checks may import modules, inspect flags, allocate tiny tensors, and compile tiny Triton/custom-op kernels. They must not:

- download VAE, text encoder, DiT, Wan, rCM, or TurboT2AV checkpoints;
- run T2V/I2V generation;
- start training;
- start the interactive TUI;
- install optional dependencies without user approval.
