# Custom TensorFlow operators

The v2 graph reaches three operator families under `models/tf_ops`:

| Family | Python wrapper | Main role | Build concern |
|---|---|---|---|
| sampling | `tf_sampling.py` | farthest-point and gather operations | CUDA source plus TensorFlow C++ ABI |
| grouping | `tf_grouping.py` | ball query, group point, and KNN helpers | CUDA kernels and registered gradients |
| 3D interpolation | `tf_interpolate.py` | three-neighbor interpolation and gradients | TensorFlow C++ wrapper and ABI |

The wrappers load sibling shared objects named `tf_sampling_so.so`,
`tf_grouping_so.so`, and `tf_interpolate_so.so`. Missing objects produce a
loader error before the v2 model can be imported.

## Build checklist

1. Select the TensorFlow version first; use its Python module to locate
   `tensorflow/include`, `tensorflow`, and the framework library rather than
   retaining the old `/usr/local/...` paths.
2. Confirm `nvcc`, `g++`, CUDA headers, `libcudart`, and the CUDA version are
   mutually compatible with that TensorFlow build.
3. Compile the CUDA object or source for each family, then link the shared
   object with `-shared -fPIC`, TensorFlow headers/framework, CUDA runtime, and
   the ABI flag required by the selected wheel.
4. Keep generated `.so` files beside their wrapper only in the isolated build
   environment. Do not commit or bundle them as portable skill assets.
5. Load each wrapper in a fresh Python process. Then run its native op test on
   the selected device. A successful compile alone is not a correctness test.

The historical shell scripts are evidence, not portable commands: they embed
Python 2.7/TensorFlow and CUDA-8 paths and an ABI flag. Adapt them to discovered
paths and record the exact compiler command in private build logs.

## Failure interpretation

- `No such file or directory` for a `.so`: compile the matching family or fix
  the working tree/package placement.
- `undefined symbol` or `GLIBCXX` error: TensorFlow wheel, compiler, C++ ABI,
  or system library mismatch; rebuild with the selected environment.
- `CUDA_ERROR_INVALID_DEVICE_FUNCTION`: kernel/toolkit architecture mismatch;
  verify the target GPU and CUDA toolkit, then rebuild.
- wrapper import succeeds but native test cannot place `/gpu:0`: framework
  CUDA visibility is missing; do not downgrade this to a CPU proof.
- v1 imports while v2 fails: expected when only the pure TensorFlow v1 path is
  available; route v2 requests back to this compatibility gate.
