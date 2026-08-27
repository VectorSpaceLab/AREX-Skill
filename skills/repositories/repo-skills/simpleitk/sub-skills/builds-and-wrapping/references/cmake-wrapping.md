# CMake and Wrapping Reference

SimpleITK uses CMake for its C++ core, SWIG for language bindings, and `scikit-build-core` for the Python source package build.

## CMake Entry Points

- `SuperBuild/`: recommended full source build entry point; fetches/builds known-compatible external projects.
- Top-level source directory: direct build entry point; requires dependencies such as ITK and SWIG to be supplied or discoverable.
- `Wrapping/<Language>/`: language wrapper subprojects can be configured independently after SimpleITK libraries/headers are available.
- `Wrapping/Python/Packaging/pyproject.toml.in`: generated Python packaging template used from the build tree.

## Core Build Options

Common options visible in the checkout include:

| Option | Meaning |
| --- | --- |
| `BUILD_TESTING` | Enables CTest tests when configured on. |
| `BUILD_EXAMPLES` | Builds examples in SuperBuild flows when enabled. |
| `BUILD_SHARED_LIBS` | Controls shared/static core libraries; Python wheels generally use static-style packaging defaults. |
| `SimpleITK_BUILD_DISTRIBUTE` | Removes local git hash suffix for official distribution builds. |
| `SimpleITK_USE_ELASTIX` | Enables optional elastix/transformix wrapper support when dependencies are built/found. |
| `SimpleITK_INT64_PIXELIDS` | Keeps 64-bit integer pixel IDs enabled; required for 64-bit compilation in this checkout. |
| `CMAKE_BUILD_TYPE` | Single-config build type such as `Release`, `Debug`, or `MinSizeRel`. |
| `ITK_DIR` | CMake package directory for direct builds against an existing ITK. |

Use CMake CLI definitions in the form `-DNAME:TYPE=VALUE`, for example:

```bash
cmake -S SimpleITK/SuperBuild -B SimpleITK-build -DWRAP_PYTHON:BOOL=ON -DBUILD_TESTING:BOOL=ON
```

## Language Wrapping Model

`CMake/sitkLanguageOptions.cmake` controls wrapping discovery:

- `WRAP_DEFAULT=ON` tries to find supported languages and enables wrappers when dependencies are found.
- `WRAP_DEFAULT=OFF` disables automatic language detection unless a specific `WRAP_<LANGUAGE>` option is set.
- Setting `WRAP_<LANGUAGE>=ON` makes the corresponding language dependency required.
- Setting `WRAP_<LANGUAGE>=OFF` prevents discovery and wrapping for that language.

Supported wrapper options in this checkout include:

| Option | Dependencies and notes |
| --- | --- |
| `WRAP_PYTHON` | Requires Python interpreter and development module support; top-level Python packaging turns this on and `WRAP_DEFAULT` off. |
| `WRAP_JAVA` | Requires Java development/runtime tools and JNI. |
| `WRAP_CSHARP` | Requires C# compiler/runtime support; disabled for MinGW in the CMake logic. |
| `WRAP_R` | Requires R and is disabled by default on Windows. |
| `WRAP_LUA` | Requires Lua library and matching interpreter version. |
| `WRAP_TCL` | Requires Tcl/Tk library and interpreter paths. |
| `WRAP_RUBY` | Requires Ruby executable, includes, and libraries. |

If a requested language wrapper is not generated, inspect the matching `WRAP_<LANGUAGE>` option plus the language-specific executable, include, and library variables in the CMake cache.

## Generated Wrapper Layout

`Wrapping/CMakeLists.txt` adds language subdirectories conditionally based on `WRAP_*` flags and defines a top-level `dist` target for package generation. SWIG is used to generate language bindings from interface files; language-specific subdirectories then build native modules, JAR/native libraries, C# libraries, R packages, or similar artifacts.

For Python, `Wrapping/Python/CMakeLists.txt`:

- Sets `WRAP_PYTHON` on for the Python wrapper project.
- Finds Python interpreter and development components.
- Uses SWIG flags such as `-keyword`, `-doxygen`, optional `-threads`, and optional `-flatstaticmethod`.
- Emits the Python module into a generated `SimpleITK` package directory.
- Installs generated `SimpleITK.py`, package support files, and the native extension as the `Python` component.
- Configures a build-tree `pyproject.toml` and packaging CMakeLists file.
- Adds a Python `dist.Python` target when Python wheel creation is enabled.

## Python Packaging Details

The source checkout top-level `pyproject.toml` is the key fact for `pip install .`:

- `build-backend = "scikit_build_core.build"`.
- `requires-python = ">=3.10"`.
- `tool.scikit-build.minimum-version = "0.11"`.
- CMake requirement for the Python source build is `>=3.26.1`.
- Default CMake defines include `WRAP_DEFAULT=OFF`, `WRAP_PYTHON=ON`, `BUILD_TESTING=OFF`, `BUILD_EXAMPLES=OFF`, `BUILD_SHARED_LIBS=OFF`, and `SimpleITK_BUILD_DISTRIBUTE=ON`.
- Python `>=3.11` uses `wheel.py-api = "cp311"` in the scikit-build overrides.

The build-tree Python packaging template also uses `scikit-build-core` and includes pytest configuration for tests packaged with the generated wrapper project.

## Python Limited API

`Wrapping/Python/CMakeLists.txt` enables the Python limited API by default only when the build has sufficient support:

- CMake version at least `3.26`.
- SWIG version at least `4.2.0`.
- Python version at least `3.11.0`.
- Python `Development.SABIModule` support when the limited API is active.

When `SKBUILD_SABI_VERSION` is `3.11`, the Python wrapper uses the limited API; unsupported SABI versions are fatal. Free-threaded Python builds with SOABI ending in `t` require CMake `>=3.30` in this checkout to avoid linking the wrong Python library.

## SWIG Expectations

- Direct builds require SWIG `>=4.3` according to the source build documentation.
- The SuperBuild SWIG external project targets SWIG `4.4.1` in this checkout.
- On Windows, SuperBuild can use a prebuilt `swigwin` archive.
- On non-Windows platforms, SuperBuild can build SWIG and PCRE2, with optional git-sourced SWIG when explicitly requested.
- Missing SWIG or mismatched SWIG/Python/CMake versions often surface as CMake configure failures, not Python import errors.

## Optional Elastix and Transformix

The top-level CMake option is:

```bash
-DSimpleITK_USE_ELASTIX:BOOL=ON
```

Important facts:

- The default is off.
- When enabled, SimpleITK adds the elastix/transformix wrapper include directory and links `SimpleElastix` into the wrapper-visible libraries.
- The SuperBuild contains `External_Elastix.cmake`, which builds elastix with selected components and sets `Elastix_DIR`.
- Source files include `Code/ElastixTransformixWrappers` and examples under `Examples/Elastix`.
- The inspected wheel did not expose `sitk.ElastixImageFilter` or `sitk.TransformixImageFilter`; a future agent should treat missing classes as an install/build capability issue, not a typo.

Use the `registration-transforms` sub-skill for parameter maps and runtime elastix/transformix workflows after confirming these classes exist in the installed build.

## Wrapper Triage Checklist

1. Confirm the installed package version and import path with `import SimpleITK as sitk`.
2. Confirm whether the feature is expected in a binary wheel or needs a source build.
3. Inspect CMake cache for `WRAP_DEFAULT`, requested `WRAP_<LANGUAGE>`, and language dependency variables.
4. For Python, verify Python version, development headers/module support, CMake version, SWIG version, and SABI settings.
5. For Java/C#/R/Lua/Tcl/Ruby, verify the corresponding compiler/interpreter/library variables all point to one consistent runtime family.
6. For elastix/transformix, verify `SimpleITK_USE_ELASTIX=ON` at configure time and confirm `hasattr(sitk, "ElastixImageFilter")` after install.
