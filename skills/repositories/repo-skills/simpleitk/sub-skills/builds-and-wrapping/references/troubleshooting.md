# Build and Wrapping Troubleshooting

Use this page to triage install/build failures without immediately starting a source build.

## `pip install simpleitk` Tries To Build From Source

Likely causes:

- The Python version, platform, or architecture has no compatible wheel.
- `pip` is too old to recognize wheel tags, stable ABI tags, or package-name normalization.
- The user requested a pre-release or source checkout install.

Actions:

1. Upgrade `pip` in the active environment.
2. Confirm Python version and platform compatibility with available wheels.
3. Try conda-forge if the project can use conda.
4. If source build is required, warn that it uses CMake/SWIG/native compilation and may fetch/build ITK.

## Old Pip or Wheel Tags

Symptoms:

- Pip reports no matching distribution despite a supported Python/platform.
- Pip downloads an sdist or starts CMake unexpectedly.
- Stable ABI wheels are ignored.

Actions:

```bash
python -m pip install --upgrade pip
python -m pip install --only-binary=:all: simpleitk
```

Use `--only-binary=:all:` as a diagnostic to force a clear error instead of silently compiling from source.

## Conda Channel Mixing

Symptoms:

- Import fails with missing shared libraries.
- Conda solves to unexpected dependency versions.
- A package works in one environment but not another.

Actions:

- Prefer a fresh conda-forge-only environment.
- Use `--channel conda-forge --override-channels` when creating the environment.
- Avoid mixing `defaults` and `conda-forge` for SimpleITK unless the user intentionally manages ABI compatibility.

## `import SimpleITK` Fails After Install

Check:

```python
import SimpleITK as sitk
print(sitk.Version())
```

Common causes:

- Installing into a different Python than the one used to run code.
- Platform shared-library load errors.
- Incomplete C#/Java native library setup for non-Python wrappers.
- A source build failed but left partial artifacts.

For Python, verify `python -m pip show simpleitk` in the same interpreter used by the application.

## `ITK_DIR` Is Missing

Likely cause: the user configured the top-level source directory when they expected SuperBuild behavior.

Actions:

- For a full source build, configure `SimpleITK/SuperBuild` instead of the top-level source.
- For a package-maintainer direct build, supply `ITK_DIR` pointing to a compatible ITK CMake package directory.
- If switching modes, start from a clean build directory to avoid stale cache variables.

## CMake Cannot Download Over HTTPS

Symptoms include `Unsupported protocol` while ExternalData or dependency downloads use `https`.

Actions:

- Use a CMake build compiled with SSL support.
- Provide dependencies or data through the build system’s supported cache mechanisms.
- Do not diagnose this as a SimpleITK Python API issue.

## Windows Path Length Failures

Symptoms:

- CMake errors about ITK source path length.
- `pip install` from source fails while using a long temporary directory.
- Visual Studio or build tools fail on generated paths.

Actions:

- Use short source, build, and temporary paths.
- Avoid spaces in source checkout paths.
- On Windows source installs through pip, set short `TEMP` and `TMP` paths before invoking pip.
- Prefer binary wheels when possible.

## Compiler, CMake, or SWIG Failure

Likely causes:

- CMake version too old for the selected build path.
- SWIG missing or below the required version.
- Python development headers/module support missing.
- Compiler not supported or not in the environment.
- Multiple Python installations produce inconsistent CMake cache variables.

Actions:

1. Decide whether the task should use a binary instead.
2. For SuperBuild, let SuperBuild provide matching SWIG/ITK where possible.
3. For direct builds, explicitly set dependency variables in the CMake cache.
4. For Python wrappers, confirm all `Python_*` CMake variables point to the same Python installation.
5. Reconfigure in a fresh build directory after changing dependency roots.

## Free-Threaded Python Failure

The Python wrapper CMake logic detects free-threaded Python SOABI values and requires CMake `>=3.30` for correct library linking. If the user is on free-threaded Python and gets configure or import-link failures, upgrade CMake or choose a non-free-threaded supported Python.

## Missing Java, C#, R, Lua, Tcl, or Ruby Wrapper

Likely causes:

- `WRAP_DEFAULT=OFF` and the language-specific `WRAP_<LANGUAGE>` was not enabled.
- The language compiler/interpreter/dev libraries were not found.
- A requested `WRAP_<LANGUAGE>=ON` made missing dependencies fatal.
- Platform-specific rules disabled a wrapper, such as R on Windows defaults or C# with MinGW.

Actions:

- Inspect `WRAP_DEFAULT` and `WRAP_<LANGUAGE>` in `CMakeCache.txt`.
- Check the language-specific variables listed in `sitkLanguageOptions.cmake`.
- Keep interpreter, headers, and libraries from the same installation family.
- Build a narrower wrapper target after dependencies are corrected.

## Missing `ElastixImageFilter` or `TransformixImageFilter`

Symptoms:

```python
import SimpleITK as sitk
hasattr(sitk, "ElastixImageFilter")  # False
hasattr(sitk, "TransformixImageFilter")  # False
```

Interpretation:

- These classes are optional and build-dependent.
- The inspected wheel did not expose them.
- Source files and examples exist, but availability requires a build configured with elastix support.

Actions:

- Do not treat class absence as a spelling issue.
- If the task is about ordinary registration, use `ImageRegistrationMethod` and route to `registration-transforms`.
- If elastix is required, plan a source build with `SimpleITK_USE_ELASTIX=ON` and verify class presence after installation.

## C# Native DLL Failure

A C# application can fail with a `DllNotFoundException` for `SimpleITKCSharpNative` when the native library is not copied or discoverable. The C# setup requires both the managed DLL and native DLL, with the native DLL copied to the output directory or otherwise discoverable by the runtime.

## Java Native Library Failure

A Java application can fail with `UnsatisfiedLinkError` for `SimpleITKJava` when the JNI native library directory is not configured. The Java setup requires both the JAR and the platform native library, with the native library directory passed through IDE settings or `java.library.path`.

## PCRE or Xcode Failure In SuperBuild

On macOS, PCRE build failures in SuperBuild can indicate missing or misconfigured Xcode command-line tools. Install or reset command-line tools before rerunning the build.

## Test Data Missing

SimpleITK test data is not all stored directly in the source repository. CTest/build flows may download data through CMake ExternalData. If data downloads fail, diagnose network/SSL/cache behavior separately from code test failures.
