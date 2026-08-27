# Troubleshooting shared APIs, utilities, and custom ops

Use this guide before opening source files. It maps symptoms to the shared API/custom-op layer owned by this sub-skill.

## Fast triage commands

```bash
# TensorFlow/custom-op split
python scripts/inspect_custom_ops.py --repo-root /path/to/pointnet2 --require tensorflow
python scripts/inspect_custom_ops.py --repo-root /path/to/pointnet2 --try-load --require custom-ops

# CPU baseline graph, no PointNet++ custom ops required
python scripts/smoke_pointnet_baseline.py --repo-root /path/to/pointnet2 --batch-size 2 --num-point 16

# Provider/pc_util smoke
python scripts/smoke_geometry_utils.py --repo-root /path/to/pointnet2
```

## TensorFlow 1.x vs TF2-only environments

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `AttributeError: module 'tensorflow' has no attribute 'contrib'` | `utils/tf_util.py` uses `tf.contrib.layers.xavier_initializer` and `tf.contrib.layers.batch_norm`. | Use a TF1.x-compatible environment such as TensorFlow 1.15 for model graph work. Do not claim TF2 import readiness is enough. |
| `AttributeError: module 'tensorflow' has no attribute 'variable_scope'` or `get_variable` failures | TF2 eager/compat behavior rather than TF1 graph semantics. | Use TF1 or a carefully ported `tf.compat.v1` path; the original repo is not TF2-native. |
| Baseline smoke fails before custom-op inspection | The CPU baseline still depends on `tf_util.py` and thus on TF1 semantics. | Fix TensorFlow first; custom ops are not involved in `pointnet_cls_basic`. |

## Missing custom-op libraries

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `OSError: ... tf_sampling_so.so: cannot open shared object file` | `tf_ops/sampling/tf_sampling.py` loads `tf_sampling_so.so` at import time and it is absent. | Compile/load custom ops or use `pointnet_cls_basic` only. |
| Importing `pointnet_util.py` fails even though TensorFlow imports | One of `tf_sampling`, `tf_grouping`, or `tf_interpolate` failed during import. | Run `inspect_custom_ops.py --repo-root <repo> --try-load --require custom-ops`. |
| PointNet++ model graph does not build but `pointnet_cls_basic` does | PointNet++ model imports traverse custom-op wrappers; CPU baseline does not. | Treat custom-op path as blocked until `.so` load succeeds. |

## ABI, CUDA, and toolchain mismatch

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `undefined symbol` from `tf.load_op_library` | Library compiled against incompatible TensorFlow headers/lib or wrong C++ ABI. | Rebuild using active `tf.sysconfig.get_compile_flags()` / `get_link_flags()` and matching `_GLIBCXX_USE_CXX11_ABI`. |
| `libcudart.so.*` not found | Linked CUDA runtime is missing from runtime library path. | Fix `LD_LIBRARY_PATH`, `CUDA_HOME`, or rebuild against the available toolkit. |
| `nvcc: command not found` | NVIDIA driver/GPU is present but CUDA toolkit is not installed. | Install compatible CUDA toolkit or mark native PointNet++ op path optional/blocked. |
| Original compile script points to `/usr/local/cuda-8.0` or `/usr/local/lib/python2.7/dist-packages/tensorflow/include` | Source scripts are CUDA 8 / Python 2 / TF1.2-era recipes. | Do not run blindly; adapt paths dynamically as described in `custom-ops.md`. |

## Geometry dependency failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `No module named eulerangles` while importing `pc_util.py` | `pc_util.py` imports `eulerangles.euler2mat` at top level. | Install the correct `eulerangles` package or use a compatibility adapter before using rendering helpers. |
| `No module named plyfile` | PLY I/O dependency missing. | Install `plyfile`; then re-run `smoke_geometry_utils.py`. |
| `NameError: name 'xrange' is not defined` from `provider.py` | Python 2-era code path. | Add a Python 3 compatibility shim (`xrange = range`) or run in Python 2 inspection env. Bundled smoke applies the shim. |
| `IndexError` inside `point_cloud_to_volume` | Points outside assumed range or exactly at `+radius` bin edge. | Normalize/clip points into `[-radius, radius)` and ensure shape is `N x 3`, not `B x N x 3` for the single-cloud function. |
| PLY round-trip fails after dependencies pass | Data shape or dtype issue, not an import issue. | Verify array is `N x 3`, numeric, finite, and writable destination path exists. |

## Visualization renderer failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `OSError` loading `render_balls_so` | Renderer shared library missing. | Run `bash scripts/compile_render_balls_so.sh --repo-root <repo> --out-dir <repo>/utils`. |
| OpenCV GUI/window error at import time | `show3d_balls.py` opens a GUI window during import. | Avoid importing in headless sessions; use `pc_util.draw_point_cloud` for non-interactive software rendering where possible. |
| Compile fails for `render_balls_so.cpp` | Missing `g++` or incompatible compiler flags. | Run helper with `--dry-run`, check compiler, and adjust `--abi` if needed. This renderer is independent of TensorFlow custom ops. |

## Python 2 vs Python 3 source syntax

Some source files and test blocks contain Python 2 `print` statements. Even if your workflow only needs static guidance, Python 3 may fail to parse those files. Prefer the bundled scripts and references for inspection. If a user explicitly needs native legacy execution, use a Python 2/TF1 environment and report unsupported modern paths clearly.

## Routing reminders

- If the user asks why ModelNet/ShapeNetPart/ScanNet training fails because of a missing custom op, diagnose the shared custom-op issue here, then route back to the workflow sub-skill for dataset/command details.
- If the user asks only for a safe CPU smoke, prefer `smoke_pointnet_baseline.py` and do not imply PointNet++ training is verified.
- If `inspect_custom_ops.py` reports TensorFlow success but missing `.so` files, explicitly state: TensorFlow is ready; PointNet++ custom-op path is not ready.
