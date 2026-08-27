# Backend Troubleshooting

Start with the symptom, backend, install mode, CUDA/device stack, and whether the user is in an installed package or source checkout. Prefer read-only probes before reinstalling or rebuilding.

## First Probes

```bash
python -m lmdeploy check_env
python sub-skills/backend-extension/scripts/inspect_backend_config.py --json
python - <<'PY'
import lmdeploy
from lmdeploy import PytorchEngineConfig, TurbomindEngineConfig
print('lmdeploy', getattr(lmdeploy, '__version__', 'unknown'))
print(PytorchEngineConfig())
print(TurbomindEngineConfig())
PY
```

If a command runs multiprocessing or distributed backends, put it under a Python main guard:

```python
if __name__ == '__main__':
    main()
```

## Missing `_turbomind`

Symptoms:

- `ModuleNotFoundError: No module named '_turbomind'`.
- TurboMind fallback warning followed by PyTorch backend selection.
- TurboMind CLI/API fails while PyTorch config imports work.

Likely causes and recovery:

1. Wheel without TurboMind extension: install a prebuilt package that includes TurboMind support, commonly the package extra that includes backend dependencies.
2. Running TurboMind commands from an LMDeploy source root shadows the installed extension layout: run from another working directory or build/link the extension for source development.
3. Source build produced extension for a different Python than runtime: rebuild with the same Python executable used to run LMDeploy.
4. `LMDEPLOY_TARGET_DEVICE` or `DISABLE_TURBOMIND` excluded the extension during install/build.

Safe decision point: if the user only needs PyTorch backend, use `PytorchEngineConfig` rather than repairing TurboMind. If they require TurboMind, choose prebuilt wheel first unless they are actively developing C++/CUDA code.

## `libnccl.so.2` Not Found

Symptoms:

- Import or startup error naming `libnccl.so.2`.
- Multi-GPU/TurboMind startup fails before model execution.

Recovery:

- Confirm package and CUDA dependency install with `python -m lmdeploy check_env`.
- Ensure the NCCL package matching the CUDA runtime is installed.
- Add the NCCL library directory to `LD_LIBRARY_PATH` only for the current shell/session; avoid baking local absolute paths into reusable scripts or skills.
- If using containers, verify the container CUDA/NCCL stack matches the host driver expectations.

## `cudaFreeAsync` Symbol Error

Symptom:

- `symbol cudaFreeAsync version libcudart.so.11.0 not defined ...`.

Cause:

- CUDA runtime/toolkit is too old for LMDeploy's CUDA runtime requirements. `cudaFreeAsync` requires CUDA 11.2 or newer.

Recovery:

- Use a wheel built for the installed CUDA runtime or update the CUDA runtime/toolkit/container image.
- Avoid mixing system `libcudart` ahead of the package/container CUDA libs in `LD_LIBRARY_PATH`.

## Python Version Mismatch After Compile

Symptoms:

- Extension exists after build but import fails in runtime Python.
- Rebuilding from source appears successful, but `python -m lmdeploy check_env` still cannot import TurboMind.

Recovery:

- Rebuild using the same `sys.executable`/environment that will run LMDeploy.
- For setup/CMake builds, ensure Python root/executable CMake options point to the target environment.
- Remove stale build directories before rebuilding if switching Python versions.
- Do not copy extension artifacts between Python minor versions.

## CUDA OOM And Cache Tuning

Symptoms:

- TurboMind allocator OOM such as `[TM][ERROR] CUDA runtime error: out of memory`.
- OOM during long prompt prefill or high concurrency.
- PyTorch scheduler/cache tests pass but real deployment fails on startup or first large request.

Recovery order:

1. Lower `cache_max_entry_count`.
2. Lower `session_len` if long context is unnecessary.
3. Lower `max_batch_size` for concurrency-heavy configs.
4. Lower `max_prefill_token_num` for prefill peak memory.
5. Disable prefix caching if many unrelated prefixes retain too much cache.
6. Consider KV cache quantization (`quant_policy=8` or `4`) only after backend support is confirmed.

Example:

```python
from lmdeploy import TurbomindEngineConfig
backend_config = TurbomindEngineConfig(cache_max_entry_count=0.2, session_len=4096)
```

For PyTorch, remember `cache_max_entry_count` must be between `0` and `1`; for TurboMind it only needs to be positive and may be interpreted as a fraction or block count.

## Invalid `quant_policy`

Symptoms:

- `ValueError: invalid quant_policy`.
- Assertion failure: `invalid quant_policy for TurboMind, FP8 quantization is not supported`.
- Assertion failure: KV cache quantization only works for CUDA/Ascend.

Recovery:

- Use enum/int values exposed by `QuantPolicy`: `0`, `4`, `8`, `16`, `17`, `42`.
- TurboMind: use `0`, `4`, or `8`; do not use FP8 policies.
- PyTorch: FP8 policies can be accepted by config but still require supported device/kernels/model path.
- Non-CUDA/non-Ascend PyTorch devices cannot use positive KV quantization.

## Optional Triton/Torch/Transformer Ranges

Symptoms:

- Import errors for `triton`, CUDA kernels, or optional modules.
- Runtime kernel failures after changing PyTorch/Triton versions.
- Feature works on PyTorch backend but fails on a specialized quantized kernel path.

Recovery:

- Use `python -m lmdeploy check_env` to capture installed `torch`, `transformers`, `triton`, `fastapi`, and `pydantic` versions.
- Prefer LMDeploy's documented/runtime requirements for the selected device rather than upgrading one dependency in isolation.
- If a feature path is optional, switch to a config that avoids that optional kernel while debugging.

## Source Build Vs Wheel Choice

Use a prebuilt wheel when:

- The user needs inference/serving rather than modifying C++/CUDA.
- The failure is a missing extension from an incomplete local source build.
- The environment matches a supported Python/CUDA wheel stack.

Build from source when:

- Editing TurboMind C++/CUDA or pybind code.
- Testing unreleased backend changes.
- The target device/backend is not covered by available wheels.

Build environment variables surfaced by LMDeploy setup:

| Variable | Effect |
| --- | --- |
| `LMDEPLOY_TARGET_DEVICE` | Selects target device requirements/build path; defaults to `cuda`. |
| `DISABLE_TURBOMIND` | When truthy, skips building TurboMind extension for CUDA target. |
| `CUDACXX` | CUDA compiler path; falls back to `CMAKE_CUDA_COMPILER` or `nvcc`. |
| `CMAKE_BUILD_TYPE` | CMake build type; defaults to `Release`. |

C++ source under `src/` should be formatted with the repository's clang-format setup; Python follows PEP8-style conventions with 120-char lines and double quotes in this repository.

## Backend/Model Edit Validation

Recommended order for maintainers editing an LMDeploy checkout:

```bash
python sub-skills/backend-extension/scripts/inspect_backend_config.py --module-map --json
pytest tests/pytorch/config/test_model_config.py
pytest tests/pytorch/paging/test_scheduler.py
pre-commit run --all-files
```

Run larger model or server tests only after targeted unit checks pass and the required GPU/model artifacts are available.
