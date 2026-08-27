# Install and Build Choices

This page helps decide whether a SimpleITK task needs a binary install, a Python source build, direct CMake, or the SuperBuild.

## Binary Installs First

Use binaries when the user wants normal SimpleITK Python usage, examples, filters, IO, registration, or NumPy integration and does not explicitly need a custom build.

### PyPI Python Wheel

```bash
python -m pip install --upgrade pip
python -m pip install simpleitk
```

Key facts:

- The Python distribution is named `simpleitk`; import it with `import SimpleITK as sitk`.
- Wheels are the preferred path for ordinary Python users on supported Windows, Linux, and macOS combinations.
- A recent `pip` is important because wheel tag, stable ABI tag, and normalized package-name support determine whether a prebuilt wheel is selected.
- If no compatible wheel exists, `pip` may fall back to an expensive source build. Warn before proceeding.

### Conda-Forge

```bash
conda create --name sitk python=3.11 simpleitk --channel conda-forge --override-channels
conda activate sitk
```

Key facts:

- Use conda-forge consistently for this environment.
- Avoid mixing `defaults` and `conda-forge` unless the user already owns the consequences; channel mixing can produce missing libraries or incompatible dependency sets.
- Change `python=3.11` to any SimpleITK-supported Python version needed by the project.

### Pre-Release and Latest Wheels

Use pre-release binaries only when the user needs a bug fix or feature from the actively developed branch and accepts pre-release risk:

```bash
python -m pip install --upgrade --pre simpleitk --find-links https://github.com/SimpleITK/SimpleITK/releases/tag/latest
```

The checkout `Version.cmake` indicates a development branch version, while the inspected wheel was `2.5.5`; do not assume the installed wheel exactly matches the current checkout.

## Non-Python Binaries

- C# and Java binaries are distributed for selected platforms through release artifacts, especially Windows.
- C# packages include managed and native libraries; applications must copy or locate the native library that matches the target architecture.
- Java packages include a JAR plus a native JNI library; the native library directory must be on the Java native library path.
- R binaries are not generally distributed; R users commonly build through an R-specific installer or from source.

## When To Build From Source

Build only when at least one of these applies:

- The user needs an unsupported binary language or platform.
- The user needs latest development-branch behavior rather than a released wheel.
- The user needs custom ITK modules, custom filters, C++ integration, or packaging integration.
- The user needs optional elastix/transformix wrappers.
- The user is contributing to SimpleITK or validating build-system changes.

Source builds are native C++/SWIG/CMake builds and can require substantial CPU, memory, disk, and time.

## Python Source Build With `pip install .`

From a source checkout, `pip install .` uses the top-level `pyproject.toml`:

- Build backend: `scikit_build_core.build`.
- Build tooling includes `scikit-build-core`, `setuptools-scm`, `swig`, `jinja2`, `jsonschema`, and `pyyaml`.
- `tool.scikit-build` sets CMake release builds, installs the `Python` component, disables tests/examples, disables shared libs, and turns on `WRAP_PYTHON` with `WRAP_DEFAULT=OFF`.
- The build can fetch/build ITK through CMake mechanisms and compile both ITK and SimpleITK when a wheel is not available.

Use this path when the user specifically wants a local Python wheel/install from the checkout and accepts the native build cost.

## SuperBuild

The recommended full source route is configuring CMake against the `SuperBuild` subdirectory:

```bash
cmake -S SimpleITK/SuperBuild -B SimpleITK-build
cmake --build SimpleITK-build --parallel
```

Key expectations:

- SuperBuild fetches/builds matching external projects such as ITK, SWIG, and GTest when needed.
- SuperBuild uses CMake ExternalProject-style builds and can download dependencies, so it is not a read-only check.
- If CMake errors that `ITK_DIR` is not set, the user probably configured the top-level source when they meant to configure `SuperBuild`.
- Use a short source/build path on Windows and avoid spaces in paths to reduce long-path problems.
- Prefer Ninja or explicit parallel build flags for speed, but scale jobs to available memory.

## Direct CMake Without SuperBuild

Use direct top-level CMake only for package maintainers or integrations that already provide the dependencies:

```bash
cmake -S SimpleITK -B SimpleITK-build -DITK_DIR=<itk-cmake-package-dir>
cmake --build SimpleITK-build --parallel
```

Additional expectations:

- ITK must already be available and compatible.
- Python with Jinja2 is required for code generation.
- SWIG is required for language wrappers.
- GTest is needed if tests are enabled.
- CMake variables are passed as `-D<name>=<value>` or edited in CMake GUI/cache tools.

## Build Tree Installation

After a successful build:

- Python package install from build tree: `python -m pip install SimpleITK-build/Wrapping/Python`.
- Python wheel target: build the `dist` target; wheel artifacts are created under the Python wrapping `dist` directory.
- R package installation is performed from the generated R packaging tree and is separate from Python packaging.

Prefer virtual environments or isolated package prefixes for build-tree installs.

## Quick Decision Matrix

| User prompt | Recommend |
| --- | --- |
| "Install SimpleITK for Python" | PyPI wheel or conda-forge binary |
| "Need SimpleITK in a conda project" | conda-forge-only environment |
| "Need latest main branch fix" | pre-release/latest wheel first; source build if no wheel fits |
| "Enable Java/C#/R wrapper from source" | SuperBuild or direct CMake with `WRAP_<LANGUAGE>=ON` and language deps |
| "Build with elastix" | Source build with `SimpleITK_USE_ELASTIX=ON`; expect optional APIs only after that build |
| "Package SimpleITK against system ITK" | Direct CMake or packaging-specific build; supply `ITK_DIR` and SWIG |
| "Just use filters/read images/register" | Do not build; route to public API sub-skills |

## Common Build Families

- Binary install failure: update `pip`, check Python version/platform tags, prefer conda-forge if compatible.
- Source build unexpectedly starts: no compatible wheel was selected; stop and confirm whether native compilation is acceptable.
- `ITK_DIR` missing: choose SuperBuild or supply an existing ITK CMake package directory.
- Windows path length: use shorter source/build/temp paths.
- CMake cannot download data/dependencies over HTTPS: use a CMake build with SSL support or provide cached dependencies through standard CMake mechanisms.
