# Cross-Cutting Troubleshooting

## Import and Package Problems

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'executorch'` | Package not installed or source checkout not on `PYTHONPATH` | Read `sub-skills/setup-build/SKILL.md`; install a wheel or run an editable source install in a Python 3.10-3.14 environment. |
| Missing `_portable_lib.so` or `_portable_lib` | Python package was built without runtime pybindings, or a source-layout import is shadowing a wheel | Rebuild/install with pybindings enabled or use a published wheel that contains pybindings; do not debug model export until runtime imports work. |
| `torchao` import errors during quantization/export recipe use | Quantization dependency missing or version mismatch | Install a compatible `torchao`; verify import before running quantization recipes. |
| `pip` dependency conflicts after using a shared environment | Inherited packages are unrelated but break `pip check` | Prefer a fresh virtualenv/conda env for reproducible builds; avoid mutating Conda `base`. |

## Export and Lowering Problems

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| `torch.export` graph break or unsupported Python control flow | Model uses data-dependent Python branches/loops or unsupported ops | Use `strict=False` for diagnosis, refactor with `torch.cond` where appropriate, or export loop bodies as separate methods. |
| Runtime shape mismatch | Dynamic dimensions were not declared or bounds are too narrow | Re-export with explicit `torch.export.Dim` bounds; keep app preprocessing within those bounds. |
| Delegation ratio lower than expected | Backend partitioner rejected unsupported nodes or dtype/layout | Read backend-specific troubleshooting; add CPU fallback intentionally and inspect partition logs. |
| `.ptd` load fails | Program-data separation path and runtime loader disagree | Use pybindings loader that accepts both `.pte` and `.ptd`; validate filenames and colocated assets. |

## Build and Backend Problems

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| Missing headers or `CMakeLists.txt` under third-party | Submodules are absent or stale | Synchronize and initialize required submodules in the user's checkout; clean stale build directories before rebuilding. |
| CMake option enabled but target missing | Required dependent option or SDK is unavailable | Reconfigure from a clean build directory and enable the dependency chain documented by the owning sub-skill. |
| Link succeeds but operators are missing at runtime | Static registration object files were pruned by linker | Use whole-archive/force-load style linker flags for kernel registration libraries. |
| Backend SDK path errors | QNN/Android/Apple/Vulkan/Arm SDK env vars or tools not available | Treat as a host prerequisite. Do not install SDKs or accept licenses without user approval. |

## When to Stop

Stop and ask for user/environment changes when the task requires vendor SDK credentials, Android/iOS devices, Arm FVP/toolchain EULA acceptance, large model downloads, a full GPU delegate build, or mutation of a user-owned environment.

