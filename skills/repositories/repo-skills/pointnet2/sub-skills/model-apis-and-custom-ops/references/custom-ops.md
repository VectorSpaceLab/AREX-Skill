# TensorFlow custom ops and compilation guide

PointNet++ models in this repository rely on TensorFlow custom operators. A working TensorFlow import is necessary but not sufficient: the custom-op wrappers call `tf.load_op_library(...)` at import time and fail immediately if the expected `.so` is absent or ABI-incompatible.

## Expected op libraries

| Wrapper module | Expected shared library | Source files | Used by |
| --- | --- | --- | --- |
| `tf_ops/sampling/tf_sampling.py` | `tf_ops/sampling/tf_sampling_so.so` | `tf_sampling.cpp`, `tf_sampling_g.cu`, `tf_sampling_compile.sh` | `farthest_point_sample`, `gather_point`, `prob_sample`; all SA models. |
| `tf_ops/grouping/tf_grouping.py` | `tf_ops/grouping/tf_grouping_so.so` | `tf_grouping.cpp`, `tf_grouping_g.cu`, `tf_grouping_compile.sh` | `query_ball_point`, `group_point`, `select_top_k`; all local-region grouping. |
| `tf_ops/3d_interpolation/tf_interpolate.py` | `tf_ops/3d_interpolation/tf_interpolate_so.so` | `tf_interpolate.cpp`, `tf_interpolate_compile.sh` | `three_nn`, `three_interpolate`; feature propagation. |

## Health-check workflow

Run the skill-owned inspector from the generated `pointnet2` skill root and pass `--repo-root` for the checkout being inspected:

```bash
python sub-skills/model-apis-and-custom-ops/scripts/inspect_custom_ops.py --repo-root /path/to/pointnet2
python sub-skills/model-apis-and-custom-ops/scripts/inspect_custom_ops.py --repo-root /path/to/pointnet2 --require tensorflow
python sub-skills/model-apis-and-custom-ops/scripts/inspect_custom_ops.py --repo-root /path/to/pointnet2 --try-load --require custom-ops
```

Interpretation:

- **TensorFlow import fails**: fix the TF1 environment before reasoning about custom ops.
- **TensorFlow imports but `.so` files are missing**: `pointnet_cls_basic` may still work, but PointNet++ models and `pointnet_util.py` imports are not ready.
- **`.so` files exist but `--try-load` fails**: treat as ABI/runtime mismatch. The usual causes are TensorFlow ABI mismatch, missing `libcudart`, CUDA version mismatch, or a compile against different headers.
- **All `.so` files load**: custom-op wrappers are likely import-ready. Then optional native op tests can be considered.

## Original compile assumptions preserved from source

The original scripts are short but not portable:

```bash
# sampling/grouping source pattern
/usr/local/cuda-8.0/bin/nvcc <op>_g.cu -o <op>_g.cu.o -c -O2 -DGOOGLE_CUDA=1 -x cu -Xcompiler -fPIC
g++ -std=c++11 <op>.cpp <op>_g.cu.o -o <op>_so.so -shared -fPIC \
  -I /usr/local/lib/python2.7/dist-packages/tensorflow/include \
  -I /usr/local/cuda-8.0/include \
  -lcudart -L /usr/local/cuda-8.0/lib64/ \
  -O2 -D_GLIBCXX_USE_CXX11_ABI=0

# 3d_interpolation source pattern
g++ -std=c++11 tf_interpolate.cpp -o tf_interpolate_so.so -shared -fPIC \
  -I /usr/local/lib/python2.7/dist-packages/tensorflow/include \
  -I /usr/local/cuda-8.0/include \
  -lcudart -L /usr/local/cuda-8.0/lib64/ \
  -O2 -D_GLIBCXX_USE_CXX11_ABI=0
```

The source also includes commented TensorFlow 1.4 variants that add:

- TensorFlow's `external/nsync/public` include directory.
- `-L<tensorflow package dir> -ltensorflow_framework`.

For TensorFlow 1.15-era environments, query metadata dynamically rather than relying on those hard-coded paths:

```bash
python - <<'PY'
import tensorflow as tf
print('version', tf.__version__)
print('include', tf.sysconfig.get_include())
print('lib', tf.sysconfig.get_lib())
print('compile flags', tf.sysconfig.get_compile_flags())
print('link flags', tf.sysconfig.get_link_flags())
print('cxx11 abi', getattr(tf.sysconfig, 'CXX11_ABI_FLAG', 'unknown'))
PY
```

## Portable compile decision checklist

1. Prove the intended Python environment imports TensorFlow 1.x and has `tf.contrib` if you also need model graph construction.
2. Check `nvcc --version`, `g++ --version`, and `nvidia-smi`. GPU visibility alone is not enough; a compatible CUDA toolkit and headers are required.
3. Prefer TensorFlow-reported include/link flags from `tf.sysconfig.get_compile_flags()` and `tf.sysconfig.get_link_flags()`.
4. Match `_GLIBCXX_USE_CXX11_ABI` to the TensorFlow wheel. The source used `0`; many TF1 wheels also require `0`, but do not assume without checking.
5. Compile in each op directory so relative source names and output library names match wrapper imports.
6. Re-run `inspect_custom_ops.py --try-load --require custom-ops` after compilation.
7. Only then run optional native tests.

## Optional native tests

Reference-only tests in the source are useful backend probes, not guaranteed portable runtime scripts:

| Test | What it checks | Native requirement |
| --- | --- | --- |
| `tf_ops/grouping/tf_grouping_op_test.py` | `query_ball_point`, `group_point`, and `GroupPoint` gradient with shape `(1,128,16) -> (1,8,32,16)`. | TF1 test session, GPU device path in source, compiled grouping op. |
| `tf_ops/3d_interpolation/tf_interpolate_op_test.py` | `three_nn`, `three_interpolate`, and interpolation gradient with shape `(1,8,16) -> (1,128,16)`. | TF1 test session and compiled interpolation op. |
| `tf_ops/sampling/tf_sampling.py` `__main__` block | Probabilistic mesh sampling, `gather_point`, and farthest point sampling. | Python 2 syntax in source block, GPU device path, compiled sampling op. |

If a user asks for full PointNet++ native verification, report any missing backend piece explicitly rather than silently falling back to the CPU baseline.

## Common failure signatures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `OSError: ... tf_sampling_so.so: cannot open shared object file` | Expected library is absent. | Compile the op or use CPU baseline only. |
| `undefined symbol` during `tf.load_op_library` | Compiled against incompatible TensorFlow headers/lib or C++ ABI. | Rebuild with the active TensorFlow's `tf.sysconfig` flags and matching ABI. |
| `libcudart.so.*: cannot open shared object file` | Runtime cannot find CUDA libraries used at link time. | Fix `CUDA_HOME`/`LD_LIBRARY_PATH` or rebuild against available CUDA runtime. |
| `nvcc: command not found` | CUDA toolkit not installed even if NVIDIA driver is visible. | Install compatible toolkit or mark custom-op path blocked/optional. |
| `No module named tf_sampling` when importing models | `tf_ops/sampling` not on `sys.path` or wrapper failed before import. | Add repo `utils`/`tf_ops/*` paths as the source does, then check `.so` readiness. |
| TF2 import succeeds but model fails with `tf.contrib` missing | Modern TensorFlow package, not TF1 semantics. | Use TensorFlow 1.15-compatible environment for source models. |

## Relationship to renderer build

`utils/show3d_balls.py` uses a separate `render_balls_so.so` built from `utils/render_balls_so.cpp`. Use `scripts/compile_render_balls_so.sh` for that helper. It does not compile TensorFlow ops and does not make PointNet++ models custom-op-ready.
