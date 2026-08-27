# Runtime Integration

## Python Host Validation

Use Python runtime validation after writing `.pte` when pybindings are installed:

```python
from executorch.runtime import Runtime
runtime = Runtime.get()
program = runtime.load_program("model.pte")
method = program.load_method("forward")
outputs = method.execute([input_tensor])
```

If `executorch.runtime` fails because `_portable_lib` is missing, rebuild/install runtime pybindings before interpreting model failures.

## C++ High-Level Module Pattern

Use the `Module` extension when dynamic allocation and convenience wrappers are acceptable:

```cpp
#include <executorch/extension/module/module.h>
#include <executorch/extension/tensor/tensor.h>

using namespace executorch::extension;
Module module("model.pte");
float input[1 * 3 * 224 * 224] = {};
auto tensor = from_blob(input, {1, 3, 224, 224});
auto result = module.forward(tensor);
```

## Android and Apple Runtime Notes

- Android Java/Kotlin loads models through the ExecuTorch Android bindings; native C++ can use the same C++ runtime concepts with an NDK build.
- Apple frameworks and Swift Package Manager flows need platform-specific packaged libraries and linker settings. Route build setup to `setup-build` and backend choice to `backend-selection`.

## Validation Order

1. Eager PyTorch output with representative input.
2. Export/lowering completes and writes `.pte`.
3. Python runtime loads and executes when pybindings exist.
4. C++ or mobile runtime loads the same artifact.
5. Backend/device execution is compared against host behavior with tolerances appropriate to quantization/backend precision.

