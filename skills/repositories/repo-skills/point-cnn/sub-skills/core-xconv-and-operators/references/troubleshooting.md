# Core operator troubleshooting

Use the symptom first, then validate the smallest graph or prerequisite that
can distinguish the listed causes. Do not paper over a backend failure by
switching a required FPS workflow to CPU and calling it verified.

| Symptom | Likely cause | Recovery and stopping rule |
|---|---|---|
| `AttributeError: module 'tensorflow' has no attribute 'contrib'` or `tf.layers` | TensorFlow 2.x is installed, or a compatibility shim is incomplete. | Run `python scripts/check_tensorflow_api.py --graph-smoke`. Use an isolated TensorFlow 1.x environment with the legacy APIs, preferably the verified 1.15 line for this snapshot. A TensorFlow 2 import alone is not compatible. Do not rewrite `tf.contrib` calls during a graph-adaptation task unless the port is explicitly requested. |
| `tf.placeholder`, `tf.Session`, or queue/iterator construction reports eager-mode errors | Eager execution is enabled. | Confirm the checker reports graph mode. In a deliberate port, disable eager execution before graph construction and replace every removed API; for the unported implementation, use native TensorFlow 1.x instead. Do not claim that `tf.compat.v1` alone restores `tf.contrib`. |
| `InvalidArgumentError` from `TopKV2`, often mentioning `k` | `K*D` is larger than the current source point count `M`, or `K` itself exceeds `M` in an inverse-density call. | Print the point count entering each layer, check `K*D <= M`, reduce `K`/`D`, or preserve more points. Check the layer's actual `pts`, not only the original input size. |
| `P` is larger than the available input point count, or `tf.slice`/`GatherNd` fails | A downsampling query count is invalid for `random`, `ids`, or `fps`; a linked feature tensor also has too few rows. | Keep `0 < P <= M` for downsampling, use `P=-1` only for all current points, and validate every link's row count. For a decoder, validate both indexed layer outputs and inherited `P`. |
| Concatenation says dimensions differ on axis 1 or the final channel count is unexpected | `data_dim` does not match the feature tensor, a link is sliced to a different `P`, or global features added `C//4` channels. | Track `[N,P,channels]` after each layer. Ensure coordinates are exactly three channels, features are `data_dim-3`, links share `P`, and the head accounts for the optional global widening. |
| `Unknown sorting method!` or the process exits while sorting | The method is not `None`, `l2`, or `c` plus a permutation of `xyz`. | Use a lower-case value such as `cxyz` or `cyxz`; check that each of `x`, `y`, and `z` occurs exactly once. |
| `Error: flexible links are supported only when random sampling is used!` | `links` were configured with `ids` or `fps`. | Remove links or use `sampling='random'` for this source behavior. If porting the architecture, implement and test an explicit link alignment policy rather than ignoring the error. |
| `AttributeError` from `np.fill` while building a unique KNN graph | The source's `find_duplicate_columns` helper calls `np.fill`, which is not a NumPy array-construction API. Its default `unique=True` KNN path can reach this callback. | Confirm the failure with a tiny graph. In a maintained adaptation, replace that construction with an equivalent explicitly sized integer array such as `np.ones((N, 1, P), dtype=np.int32)` and add a regression test. Preserve the intended duplicate mask; do not silently set `unique=False` in production without deciding how duplicate neighbors should behave. |
| `tf.py_func`/`PyFunc` cannot execute in a serialized or distributed graph | `inverse_density_sampling` and duplicate handling use Python callbacks and NumPy. | Use a local TF1 session for this path, or port the helper to pure TensorFlow. A successful graph build does not prove portability to SavedModel, eager mode, or remote workers. |
| `ImportError` or `NotFoundError` for `tf_sampling_so.so` | The sampling wrapper loads the shared library at import time and the sibling file is absent or named differently. | Run `python scripts/inspect_sampling_build.py --sampling-dir <sampling-dir>`. Build into the directory used by the wrapper only after all checks pass. Do not import `sampling` merely to test CPU availability. |
| `undefined symbol` while loading the sampling library, including TensorFlow C++ symbols | The library was linked against a different TensorFlow build, C++ ABI, compiler/runtime, or incompatible framework library. | Rebuild with the exact TensorFlow headers/library reported by the same Python environment. Compare `tf.sysconfig` paths and the C++ ABI setting; this legacy build recipe uses `-D_GLIBCXX_USE_CXX11_ABI=0`. Use `--check-load` after rebuilding, then run a bounded kernel smoke. If symbols still differ, stop and mark the operator unavailable rather than trying random linker flags. |
| `nvcc: command not found`, CUDA headers or `libcudart` missing | CUDA toolkit is absent or `CUDA_ROOT` points at a runtime-only installation. | Run the build diagnostic with `--cuda-root <cuda-root> --show-build-command`; install/select a toolkit compatible with the TensorFlow 1.x CUDA build. Do not download a toolkit or compile by default from the skill. |
| `nvcc` rejects the host compiler or CUDA code fails for the GPU architecture | The compiler/toolkit is too new or the legacy source lacks an architecture flag for the device. | Record `nvcc --version`, compiler version, TensorFlow CUDA build, and GPU compute capability. Use a compatible compiler/toolkit pair and an explicit architecture flag only after a maintainer reviews the change. The source kernels are legacy CUDA and do not provide a CPU fallback. |
| The library loads and a GPU graph is created, but `GatherPoint`/FPS execution hangs, times out, or reports CUDA OOM | Driver/device initialization, GPU contention, framework/toolkit mismatch, or kernel/runtime failure; loadability is not execution proof. | Use one visible, idle GPU, bound memory growth, and a tiny `[1,5,3]` or `[1,8,3]` fixture. Inspect driver/toolkit/framework logs. The pinned inspection evidence found TensorFlow 1.15 import and A100 discovery but timed out during minimal custom-op/GPU execution; keep FPS `BLOCKED_REQUIRED_BACKEND` until a bounded run completes. |
| FPS segmentation works on CPU until the sampler is reached, then has no kernel | All custom sampling kernels are registered for `DEVICE_GPU` only. | Use `sampling='random'` or `ids` only for an intentionally non-FPS graph experiment. That is not an equivalent validation of FPS-based segmentation. Maintain the CUDA prerequisite and report the substitution explicitly. |
| `FarthestPointSample expects positive npoint` | `P` or the direct `npoint` argument is zero or negative. | Use `P=-1` only in X-Conv settings where it means all points; the custom op itself requires a positive explicit count. Resolve `P` to a positive value before calling FPS. |
| `GatherPoint` rejects ranks or the last coordinate size | Input is not float32 `[B,N,3]`, indices are not int32 `[B,M]`, or batch dimensions disagree. | Cast and reshape at the boundary; assert the exact four dimensions before calling the op. Do not pass feature tensors with channels other than 3 to `gather_point`. |
| GPU discovery itself is slow or times out | Device initialization is interacting with driver state, memory pressure, or other workloads. | Treat discovery and execution as separate checks. Set a bounded timeout outside the graph process, use a less-contended device, and preserve the timeout in verification notes. Never convert “device listed” into “custom op passed.” |

## Build diagnostic and manual recipe

The bundled `scripts/inspect_sampling_build.py` checks source markers, compiler
presence, TensorFlow legacy API visibility, expected shared-library naming, and
optional loadability. It does **not** invoke `nvcc`, `g++`, a download, or a
TensorFlow session unless the user explicitly requests `--check-load` (which
only loads the library and still does not run a kernel).

When a sampling directory contains the wrapper and build sources, use
`--show-build-command` to print a command with explicit placeholders. The
important requirements are:

1. Use the same Python/TensorFlow environment for `TF_INC` and `TF_LIB` that
   will load the resulting library.
2. Compile the CUDA translation unit with position-independent code.
3. Link the C++ registration unit and CUDA object against
   `libtensorflow_framework`, the TensorFlow include tree, CUDA runtime, and
   the legacy C++ ABI setting used by this source (`0`).
4. Place the output as `tf_sampling_so.so` beside the wrapper that calls
   `tf.load_op_library`.
5. First run `--check-load`; only then run a tiny GPU `GatherPoint`/FPS session
   under a bounded external timeout.

Do not substitute a CPU implementation and report the FPS requirement as
passed. Do not use full dataset training to debug a shared-library ABI error.
