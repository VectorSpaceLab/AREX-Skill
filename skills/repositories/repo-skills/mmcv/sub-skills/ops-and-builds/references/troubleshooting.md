# MMCV Ops And Build Troubleshooting

Use the bundled checker first when a report is ambiguous:

```bash
python scripts/check_mmcv_install.py
python scripts/check_mmcv_install.py --require-ops
```

## Symptom Matrix

| Symptom | Likely cause | Concrete recovery or stop condition |
| --- | --- | --- |
| `No module named mmcv.ops` | `mmcv-lite` is installed, full `mmcv` is not installed, or package install is incomplete | If ops are needed, uninstall the conflicting variant, then install full `mmcv` with MIM or a matching wheel. If ops are not needed, route away from this sub-skill and keep `mmcv-lite`. |
| `No module named mmcv._ext` | Full native extension is absent; common after `MMCV_WITH_OPS=0`, failed source build, or lite package | Run the checker. If it reports lite/no ops, install full `mmcv` or rebuild with `MMCV_WITH_OPS=1`. Do not treat this as an MMCV bug in a known lite environment. |
| MIM downloads `.tar.gz` instead of a wheel | No matching prebuilt wheel for current Python/PyTorch/CUDA/MMCV combination | Choose a supported combination, pin a version with an available wheel, build from source, or choose `mmcv-lite` if ops are unnecessary. |
| `undefined symbol` | ABI mismatch, often PyTorch/CUDA/C++ symbols from a wheel or extension built against a different runtime | Verify PyTorch version, CUDA runtime, compiler, and MMCV wheel selector. Reinstall a matching wheel or rebuild from source in the same environment. |
| `cannot open xxx.so` | Missing shared library such as CUDA runtime, C++ runtime, or PyTorch shared object | Check that the runtime has the same CUDA/PyTorch libraries used at build time. Reinstall PyTorch or rebuild MMCV after fixing the library path/runtime. |
| `libtorch_cuda_cu.so: cannot open shared object file` | PyTorch CUDA shared library not present or not discoverable by the runtime | Reinstall the correct CUDA-enabled PyTorch build or use a CPU-only stack with CPU-built MMCV. Stop if the environment is intentionally CPU-only and user requires CUDA ops. |
| `invalid device function` or `no kernel image is available for execution` | CUDA arch mismatch; extension was not compiled for the GPU's compute capability | Set `TORCH_CUDA_ARCH_LIST` for the target GPU and rebuild, or install a wheel built for a compatible CUDA/PyTorch/GPU stack. Older GPUs are especially affected. |
| `RuntimeError: CUDA error: invalid configuration argument` | Kernel launch configuration is incompatible with the GPU or workload; docs mention poor GPU performance and thread block settings | Try a supported GPU or rebuild with adjusted kernel configuration. Stop and escalate when changing kernel constants is outside the user's maintenance scope. |
| `RuntimeError: nms is not compiled with GPU support` | MMCV extension was built without CUDA or CUDA environment was not available/correct during build | Reinstall/build full `mmcv` with CUDA enabled. Delete stale build artifacts before rebuilding. Verify with `--require-ops --require-cuda`. |
| Segmentation fault | Common causes include incompatible GCC/PyTorch/CUDA runtime or a broken native extension | Check GCC version, PyTorch CUDA availability, `import mmcv; import mmcv.ops`, and rebuild in a clean environment. Avoid GCC versions known to be problematic for the target PyTorch stack. |
| Windows unsupported Visual Studio version | CUDA toolkit and MSVC version are incompatible | Use a Visual Studio version supported by the CUDA toolkit or install a PyTorch/MMCV combination that supports the available compiler. |
| Windows PyTorch header errors such as `all_slots` or `ProfileOptionalOp::Kind` | Old PyTorch/CUDA/Windows compiler incompatibilities | Prefer upgrading PyTorch/MMCV to a supported combination. Only patch local PyTorch headers when reproducing legacy builds and the user accepts that risk. |
| Registry import errors such as `KeyError: ... is not in the ... registry` | The module registering a component was not imported; often downstream OpenMMLab usage rather than MMCV install | Import the module that performs registration or verify downstream project/MMCV compatibility. Do not reinstall MMCV unless ops/package checks also fail. |
| `ConvWS is already registered in conv layer` or downstream compatibility errors | MMCV version does not match the downstream OpenMMLab project | Check the downstream project's compatibility table and install the expected MMCV major/minor version. |

## Decision Tree

1. Does the user need `mmcv.ops`?
   - No: prefer `mmcv-lite`, route pure media/transform/CNN-builder tasks to the relevant sub-skill.
   - Yes: require full `mmcv` and continue.
2. Does `python -c "import mmcv; import mmcv.ops"` succeed?
   - No: use the package-variant and extension rows above.
   - Yes: continue to device/backend validation.
3. Is the failure device-specific?
   - CPU failure: check the exact op's CPU support and extension import.
   - CUDA/backend failure: check wheel selector, build flags, `torch.version.cuda`, `torch.cuda.is_available()`, compiler metadata, and per-op backend support.
4. Did the environment install both `mmcv` and `mmcv-lite`?
   - If yes, uninstall both variants and reinstall exactly one.

## Known Lite Inspection Behavior

In a source install made with `MMCV_WITH_OPS=0`, the distribution name is `mmcv-lite` while the import package remains `mmcv`. In that environment, `import mmcv` succeeds but `import mmcv.ops` fails with `ModuleNotFoundError: No module named 'mmcv._ext'`. This is expected lite behavior, not evidence that full ops are available.

## Safe Verification Pattern

Use checks that match the user's intent:

```bash
# Lite/non-op workflow: import package only.
python scripts/check_mmcv_install.py

# Full-op workflow: require extension-backed ops.
python scripts/check_mmcv_install.py --require-ops

# CUDA full-op workflow: require PyTorch CUDA availability and ops import.
python scripts/check_mmcv_install.py --require-ops --require-cuda
```

Do not run broad package test suites as a normal user diagnostic. Most op-level tests require a compiled full extension and some require specific devices, so use focused import and checker commands first.
