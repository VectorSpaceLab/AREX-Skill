# Packaging and release troubleshooting

## Fresh install or startup import fails

Symptoms:
- `pip install .` cannot resolve or build a dependency.
- Startup import fails before the GUI opens.
- A test around the label colormap reports a read-only NumPy assignment error.

Likely causes:
- Dependency floors allow a newer package with changed import-time behavior.
- PyQt6 or Qt platform libraries are missing for the current OS.
- Generated resources are stale or import the wrong Qt binding.

Recovery:
1. Reproduce in a fresh environment, not a long-lived development environment.
2. Run the startup smoke with `QT_QPA_PLATFORM=offscreen` in headless sessions.
3. Run the focused colormap test if the failure mentions NumPy assignment or `imgviz.label_colormap()`.
4. If resources were regenerated, inspect `resources.py` for PyQt6 imports and rerun the smoke.
5. If the crash only occurs on one Python version, repeat dependency resolution on the CI-supported Python versions to isolate a wheel or ABI issue.

## Headless Qt fails on Linux

Symptoms:
- Qt complains about an unavailable platform plugin.
- Import or tests hang or fail when no display is attached.

Recovery:
- Set `QT_QPA_PLATFORM=offscreen` for import and unit-test checks.
- If the offscreen plugin still fails, install the host Qt/XCB/EGL libraries required by PyQt6 on the target Linux image.
- Do not treat a GUI display failure as an auto-labeling model failure until the startup import path works.

## macOS PyQt install mismatch

Symptoms:
- `pip install anylabeling` on macOS does not install PyQt6.
- Imports fail with missing PyQt6 even though the package installed.

Cause:
- Package metadata excludes PyQt6 on Darwin. The documented path is to install PyQt through Conda or an equivalent macOS-compatible channel first.

Recovery:
1. Create a macOS environment with a supported Python.
2. Install PyQt6 through the documented platform channel.
3. Install AnyLabeling and run the startup smoke.
4. Add `[macos]` only when the CoreML path is required.

## GPU wheel has the wrong package name or dependency

Symptoms:
- The built artifact is named `anylabeling-...whl` instead of `anylabeling_gpu-...whl`.
- Wheel metadata still depends on `onnxruntime` instead of `onnxruntime-gpu`.
- Installing the GPU artifact shadows or conflicts with the CPU package unexpectedly.

Cause:
- The GPU release requires an explicit `pyproject.toml` rewrite before build. Changing only `__preferred_device__` is not sufficient.

Recovery:
1. Re-run the GPU build workflow steps in a disposable branch or clean checkout.
2. Verify `pyproject.toml` package name and ORT dependency before building.
3. Inspect the wheel `METADATA` after building.
4. Restore source metadata to the CPU/default state before unrelated commits.

## PyInstaller artifact cannot import onnxruntime on Windows

Symptoms:
- Executable startup fails near `onnxruntime_pybind11_state.pyd`.
- Error mentions `onnxruntime.dll` or `onnxruntime_providers_shared.dll`.

Likely cause:
- Native DLLs next to the ORT Python extension were not collected or preloaded from the bundled location.

Recovery:
1. Inspect the PyInstaller build output for `onnxruntime/capi/onnxruntime.dll` and `onnxruntime/capi/onnxruntime_providers_shared.dll`.
2. Confirm the runtime hook runs before importing ORT.
3. Keep the hook's dependency order: provider shared DLL first, then main ORT DLL.
4. Rebuild from a fresh environment after changing ORT versions.

## Translation/resource tools are missing

Symptoms:
- `pyside6-rcc`, `pyside6-lrelease`, `pyuic6`, or `pylupdate6` is not found.
- Resource regeneration produces a module that imports PySide6.

Recovery:
1. Run the bundled helper:
   ```bash
   python scripts/check_language_tools.py
   ```
2. Install the developer extra in a maintainer environment if tools are missing.
3. Re-run the appropriate generation script.
4. Verify generated imports were rewritten from PySide6 to PyQt6.
5. Run the startup import smoke.

## Real-inference tests skip or fail

Symptoms:
- `tests.test_real_inference` reports skipped classes.
- SAM3 text tests fail with no matching object even though the model loads.

Interpretation:
- Skips are expected when external model files are absent.
- SAM3 text prompts need an image that contains the requested class; a fallback sample image may not satisfy semantic assertions.

Recovery:
- For packaging-only changes, clean skips are acceptable.
- For model loading, preprocessing, ONNX runner, or prompt changes, download the relevant model folders and use a suitable prompt image before declaring real inference verified.
- Record SAM3 model size/time expectations before starting multi-GB downloads.

## Maintainer script mutates files unexpectedly

Symptoms:
- `app_info.py`, `pyproject.toml`, generated resources, or temporary specs changed after a build attempt.

Recovery:
1. Check the working tree before and after build scripts.
2. Restore `__preferred_device__` to the intended default after GPU/folder builds.
3. Restore package metadata after a GPU wheel build unless the release branch intentionally carries the rewrite.
4. Do not run upload/publish scripts unless the user explicitly requested publication and credentials are ready.
