---
name: setup-build
description: "Install and build ExecuTorch from source, including Python package
  variants, CMake presets, cross-compilation entry points, focused tests, and
  build troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# setup-build

Use this sub-skill when the user needs to install ExecuTorch, build it from a source checkout, configure CMake, diagnose build/install failures, or choose a focused validation command after a build.

## Route Here For

- Creating a Python environment for ExecuTorch development.
- Installing the Python package from source with `install_executorch.sh`, `pip install -e . --no-build-isolation`, or `EXECUTORCH_BUILD_MINIMAL`.
- Explaining full vs minimal vs editable installs, optional Python extras, nightly vs pinned PyTorch, and rebuild requirements.
- Configuring and building the C++ runtime with CMake presets or explicit `EXECUTORCH_*` flags.
- Planning Android AAR/native and Apple framework builds at the entry-point level, while treating SDKs/devices as prerequisites.
- Running focused Python, CMake, and smoke validation commands after install/build.
- Troubleshooting build failures, missing submodules, CMake/toolchain issues, Python package shadowing, and linker/static-registration problems.

## Do Not Handle Here

- Backend selection strategy or backend-specific quantization/export choices: route to `backend-selection`.
- Qualcomm/QNN SDK setup or graph preparation details: route to `qualcomm`.
- Cortex-M/bare-metal/Zephyr-specific build and flashing details: route to `cortex-m`.
- Profiling/ETDump/Inspector workflows: route to `profiling-debugging`.
- LLM/ASR model export, tokenizer, and runner flows beyond noting Makefile entry points: route to `llm-workflows`.
- Binary-size tuning beyond basic release/size flags: route to `binary-size`.

## First Response Checklist

1. Identify the requested surface: Python package, C++ runtime, Android, Apple framework, or tests/maintenance.
2. Confirm the user is in an ExecuTorch source checkout when a source build is requested. If not, give source-checkout prerequisites instead of pretending a build can run.
3. Classify hardware/vendor SDK requirements as prerequisites: Android NDK/SDK, Xcode, CUDA, Vulkan SDK, QNN SDK, Neuron SDK, or Apple GPU backends are optional unless the user requested them.
4. Prefer a minimal, focused command before a broad build: `--minimal`, a single CMake preset, a single target, or a single pytest path.
5. State expected success signals and the recovery command for stale artifacts or missing submodules.

## Primary References

- [Build and install workflows](references/build-and-install.md)
- [Test and maintenance commands](references/test-and-maintenance.md)
- [Troubleshooting matrix](references/troubleshooting.md)

## Bundled Helper

Run the bundled environment diagnostic before prescribing a long build or when triaging user errors:

```bash
python scripts/check_executorch_env.py --repo-root /path/to/executorch
```

Without `--repo-root`, it checks only the current Python/process/toolchain environment. With `--repo-root`, it also inspects an ExecuTorch checkout for expected source-build files, CMake presets, Windows symlink risk, and key submodule sentinels. The helper is read-only: it does not install packages, clone submodules, or build targets.

## Default Recommendation Patterns

| User intent | Best first action |
|---|---|
| "Install ExecuTorch from source" | Create/activate Python 3.10-3.14 env, then `./install_executorch.sh --editable` for development or `./install_executorch.sh --minimal` for a lean export/runtime package. |
| "I already installed dependencies" | Use `pip install -e . --no-build-isolation` for Python-only iteration; rerun `./install_executorch.sh` after C++/extension changes. |
| "Build C++ runtime" | Configure with `cmake -B cmake-out --preset <platform> -DCMAKE_BUILD_TYPE=Release`, then `cmake --build cmake-out --parallel <jobs>`. |
| "Build with backend X" | Add the corresponding `-DEXECUTORCH_BUILD_<BACKEND>=ON` flag only after verifying its SDK/toolchain prerequisite. Use backend-specific sub-skills for nontrivial setup. |
| "Validate install" | Start with import/package probes and one small export/runtime smoke check before `pytest` or full `ctest`. |
