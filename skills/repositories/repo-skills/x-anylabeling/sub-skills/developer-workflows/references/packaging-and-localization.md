# Packaging and localization

This reference distills executable-building and translation/resource workflows. These workflows are development and release-engineering actions: they can create or overwrite generated files, write build outputs, and depend on platform-specific tools.

## Packaging prerequisites

Use packaging only when the user needs a local executable or wants to diagnose a build plan. It is not required for normal package use.

Baseline requirements:

- Python `>=3.11`, with Python `3.12` recommended.
- The package installed with the runtime extra matching the target build: `cpu`, `gpu`, `gpu-cu11`, or `gpu-cu13`. Install only one of these extras in a single environment.
- Developer build tools, including `pyinstaller`.
- A platform-compatible Qt/PyQt stack.
- For GPU builds, a compatible ONNX Runtime GPU package and matching CUDA/cuDNN runtime libraries.

GPU build verification is local-hardware-specific. CPU package and ONNX Runtime CPU provider were verified during skill construction; GPU and TensorRT were not.

## Build script interface

The executable build helper accepts exactly one target argument. For planning or diagnosing a user-supplied build command, the recognized target values are `win-cpu`, `win-gpu`, `linux-cpu`, `linux-gpu`, and `macos`.

Target mapping:

| Target | Device env | PyInstaller spec |
|---|---|---|
| `win-cpu` | `X_ANYLABELING_DEVICE=CPU` | `x-anylabeling-win-cpu.spec` |
| `win-gpu` | `X_ANYLABELING_DEVICE=GPU` | `x-anylabeling-win-gpu.spec` |
| `linux-cpu` | `X_ANYLABELING_DEVICE=CPU` | `x-anylabeling-linux-cpu.spec` |
| `linux-gpu` | `X_ANYLABELING_DEVICE=GPU` | `x-anylabeling-linux-gpu.spec` |
| `macos` | `X_ANYLABELING_DEVICE=CPU` | `x-anylabeling-macos.spec` |

The script fails fast when:

- The target argument is missing or unrecognized.
- `pyinstaller` is not on `PATH`.
- The selected spec file is missing.
- macOS post-packaging tools are missing when building `macos`.

The script sets `X_ANYLABELING_ROOT` to the project root and writes artifacts under `dist/` through PyInstaller.

## PyInstaller spec behavior to know

- Windows CPU/GPU specs collect ONNX Runtime DLLs from the installed package. They include an ONNX Runtime DLL bootstrap hook that adds packaged DLL directories to the Windows DLL search path at runtime.
- Windows specs also collect selected MSVC runtime DLLs and Matplotlib data.
- Linux GPU spec bundles ONNX Runtime CUDA provider shared libraries when present in the installed package.
- Linux CPU and macOS specs do not include GPU provider libraries.
- The specs read the application version from package metadata/source and name the output executable accordingly.
- Spec/device mismatches are common: using a GPU target without the correct GPU runtime packages usually builds a broken or incomplete artifact.

## macOS zip and checksum

After a successful `macos` PyInstaller build, the build helper packages the newest `X-AnyLabeling-v*-macOS.app` in `dist/` into an unsigned zip. It:

1. Locates the newest macOS `.app` bundle.
2. Reads the bundle executable name from `Info.plist`.
3. Detects architecture from `lipo -info` or `file` output.
4. Creates `<app-name>-<arch>-unsigned.zip`.
5. Writes a sibling `.sha256` checksum file.

Required macOS tools for this post-step include `ditto`, `file`, `shasum`, and `/usr/libexec/PlistBuddy`.

## Packaging safety checklist

Before starting a build:

- Confirm target OS and CPU/GPU variant.
- Confirm whether the user wants a source checkout/development build or package-only runtime use.
- Confirm the active environment has the matching optional extra and `pyinstaller`.
- For GPU builds, verify the installed ONNX Runtime GPU package and CUDA/cuDNN compatibility. Do not use CPU-only verification as proof of GPU packaging.
- Warn that `dist/` and PyInstaller working directories may be overwritten.
- Do not run release publishing or release-note scripts as part of a packaging request unless the user explicitly asks for maintainer release actions.

## Localization and resource workflow

X-AnyLabeling uses Qt translation catalogs and a generated Python resource module.

Supported interface translation catalogs are:

- `en_US`
- `zh_CN`
- `ja_JP`
- `ko_KR`

Two development scripts exist conceptually:

1. **Generate translations**:
   - Scans Python files and UI files.
   - Converts `.ui` files into generated Python UI files with `pyuic6`.
   - Extracts translatable strings with `pylupdate6 --no-obsolete`.
   - Compiles each `.ts` file into `.qm` using an available Qt Linguist release compiler.
   - Rebuilds the Python resource module.

2. **Compile translations**:
   - Compiles existing `.ts` catalogs into `.qm` using `lrelease`, `lrelease-qt6`, or `pyside6-lrelease`.
   - Rebuilds the Python resource module.

Both workflows mutate generated files and should be run only in a development checkout with source-control review.

## Required localization tools

The scripts look for a Qt release compiler in this order:

1. `lrelease`
2. `lrelease-qt6`
3. `pyside6-lrelease`

Resource compilation tries multiple commands:

- `python -m PyQt6.pyrcc_main`
- `pyrcc6`
- `pyside6-rcc`
- `rcc -g python`
- an `rcc` executable next to `lrelease`

When supported, resource compilation requests zlib compression to avoid Qt runtime issues with resource entries compressed by newer defaults.

If a PySide6 or generic `rcc` command is used, generated imports are normalized from `PySide6` to `PyQt6`.

## Generated resources side effects

The resource workflow writes a generated `resources.py` module. Treat it as a build artifact:

- Do not hand-edit it.
- Expect very large diffs after resource or Qt toolchain changes.
- Review source `.qrc`, translations, icons, and UI files rather than editing the generated Python directly.
- If the application fails to import resources after regeneration, check whether the generated imports target `PyQt6` and whether the active Qt package version can read the selected resource compression.

## Troubleshooting quick checks

- `pyinstaller: command not found`: install developer dependencies or add PyInstaller to `PATH`.
- `Required file ...spec was not found`: check that the target name matches one of the five known targets.
- GPU build imports CPU provider only: the active environment likely has the CPU extra or lacks ONNX Runtime GPU provider libraries.
- Windows packaged app cannot load ONNX Runtime DLLs: inspect packaged `onnxruntime/capi` DLLs and the runtime hook behavior.
- `No Qt translation compiler found`: install Qt Linguist tools or ensure `pyside6-lrelease` is available.
- `no Qt resource compiler found`: install PyQt6/PySide6 developer tools or provide `rcc`/`pyrcc6`.
