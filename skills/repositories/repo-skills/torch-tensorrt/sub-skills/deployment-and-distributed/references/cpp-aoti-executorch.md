# C++, AOTInductor, and ExecuTorch Deployment

## C++ / libtorch with TorchScript

Use this path when the user needs a C++ application that loads a TorchScript artifact containing TensorRT-backed execution.

Requirements:

- A Torch-TensorRT build with TorchScript frontend and Torch-TensorRT runtime libraries enabled.
- libtorch matching the PyTorch version used to build/save the artifact.
- CUDA and TensorRT runtime libraries visible to the process.
- `.ts` artifact produced with `torch_tensorrt.save(..., output_format="torchscript")`.

Minimal C++ shape:

```cpp
#include <torch/script.h>

int main() {
  torch::jit::Module module = torch::jit::load("model.ts");
  // Construct CUDA tensors that match the compiled input profile.
  // auto out = module.forward({input_tensor});
}
```

Do not choose this path from a Python-only wheel or when `ENABLED_FEATURES.torch_tensorrt_runtime` is false.

## AOTInductor `.pt2`

AOTInductor packages a compiled model into a `.pt2` artifact. Torch-TensorRT subgraphs become embedded TensorRT engines and fallback PyTorch ops are compiled by AOTInductor.

Save pattern:

```python
torch_tensorrt.save(
    compiled,
    "model.pt2",
    output_format="aot_inductor",
    retrace=True,
    arg_inputs=example_inputs,
    dynamic_shapes=dynamic_shapes,
)
```

Python load pattern:

```python
import torch
model = torch._inductor.aoti_load_package("model.pt2")
out = model(*runtime_inputs)
```

Use on Linux-focused deployments and verify with the exact PyTorch/AOTInductor stack.

## Raw TensorRT engine for C++/non-PyTorch runtimes

When a user wants no PyTorch dependency, consider raw `.engine` bytes. This requires full TensorRT conversion with no fallback. The C++ application then uses TensorRT runtime deserialization and binding execution, not Torch-TensorRT's PyTorch wrapper.

Use the compilation sub-skill's serialization reference for the engine-producing API.

## ExecuTorch

Use ExecuTorch only when the user explicitly targets ExecuTorch or `.pte` artifacts. Requirements are optional and may not be installed with ordinary Torch-TensorRT wheels.

Checklist:

- Verify `executorch` package and Torch-TensorRT ExecuTorch support are installed.
- Export the model through the documented PyTorch/ExecuTorch flow.
- Ensure compile specs and external data files match the target runtime.
- Test on the target runtime, not just in the build environment.

## Troubleshooting

- `NotImplementedError: Torch-TensorRT Runtime is not available`: installed wheel lacks runtime libraries; use Python `.ep` or reinstall/build with runtime.
- C++ linker/loader errors: library path does not include libtorch, TensorRT, CUDA, or Torch-TensorRT runtime libraries.
- AOTI load fails: PyTorch/AOTInductor version mismatch or unsupported operation/package state; reproduce with a tiny `.pt2` package.
- ExecuTorch export fails: optional ExecuTorch dependencies or target backend are missing; do not substitute a normal Python export and call it equivalent.
