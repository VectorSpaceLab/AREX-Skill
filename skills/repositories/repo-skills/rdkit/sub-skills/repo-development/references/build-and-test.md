# Building and Testing RDKit Changes

RDKit is a compiled C++ project with Python wrappers. A safe test plan depends on whether a change touches C++, wrappers, Python package files, data/docs, or build configuration.

## Build Model

- The top-level CMake project requires modern CMake and builds C++ libraries plus optional components.
- The project uses C++20 and C99.
- Python wrappers are enabled by default through `RDK_BUILD_PYTHON_WRAPPERS=ON`.
- Build outputs include runtime binaries, libraries, archives, and Python extension modules.
- In-tree install is enabled by default by `RDK_INSTALL_INTREE=ON`, which means build/install decisions can affect the source tree layout.
- Optional features such as InChI, Avalon, PostgreSQL, CoordGen, MAE parser, PubChemShape, FreeSASA, MinimalLib, CFFI, fuzz targets, Java/SWIG wrappers, and long-running tests have separate CMake flags and dependencies.

## Configure Caveats

Before diagnosing source code, separate configuration failures from code failures:

- Missing compiler or CMake support can fail before any RDKit target builds.
- Optional dependencies should usually be disabled unless the change specifically targets them.
- Some dependencies may be fetched or discovered during CMake configure; network-restricted environments can fail on fetch-dependent paths.
- Wrapper builds require Python development compatibility with the selected interpreter.
- Tests that require optional components should not be selected unless those components were enabled.

A minimal local build command varies by platform and environment, but the shape is generally:

```bash
cmake -S . -B build -DRDK_BUILD_PYTHON_WRAPPERS=ON
cmake --build build --target <target-or-all>
```

Use repository- or environment-specific setup instructions when available; do not invent dependency paths.

## Binary Package vs Source Checkout

A binary RDKit package can verify public API facts, but it does not validate edited local C++ or wrapper code. Conversely, importing from an unbuilt source checkout often fails because compiled modules are missing.

Safe rules:

- Use binary imports outside the checkout for API inspection and examples.
- Use a built source tree for validating repository changes.
- If `from rdkit import rdBase` fails inside a checkout, diagnose checkout shadowing before editing source.
- If a test unexpectedly imports the binary package after local edits, the test did not validate the local change.

Run the bundled diagnostic from this sub-skill when in doubt:

```bash
python scripts/check_checkout_shadowing.py --json
```

## Focused Test Selection

Start narrow, then widen.

### Python-only changes

Use nearby package tests first:

```bash
python -m pytest rdkit/Chem/UnitTestDescriptors.py
python -m pytest rdkit/Chem/Draw/UnitTestDraw.py
python -m pytest Projects/DbCLI/UnitTestDbCLI.py
```

Pick test files by matching the changed module path and `UnitTest*.py` convention. Remember that `rdkit/pytest.ini` enables doctests and has ignore rules.

### C++ library changes

Build the relevant target, then run matching CTest names:

```bash
cmake --build build --target <library-or-test-target>
ctest --test-dir build -R '<target-or-area-regex>' --output-on-failure
```

Use `ctest --test-dir build -N -R '<regex>'` to list matching tests before running them.

### C++ behavior exposed to Python

Run both sides:

```bash
ctest --test-dir build -R '<cpp-test-regex>' --output-on-failure
python -m pytest <nearby-wrapper-or-package-test.py>
```

For example, a descriptor implementation change may require C++ descriptor tests and `rdkit/Chem/UnitTestDescriptors.py`. A fingerprint generator change may require `Code/GraphMol/Fingerprints` C++ tests and wrapper/Python tests for fingerprint APIs.

### Wrapper changes

Inspect the nearby `Wrap/CMakeLists.txt` for `rdkit_python_extension(...)` and `add_pytest(...)` entries. Prefer the registered wrapper test target when using CTest, then add package-level Python tests if the public import path is affected.

### Build-system changes

For CMake edits, verify configuration plus a target that exercises the changed option or module:

```bash
cmake -S . -B build <relevant-options>
cmake --build build --target <representative-target>
ctest --test-dir build -N -R '<expected-test-regex>'
```

Do not claim runtime behavior is tested from configure-only checks.

## Full Test Suites

The contributor guidance points to `ctest` from the build directory for full C++/Python registered tests and `python -m pytest` for Python-only work after a working setup.

Useful CTest options:

- `-N`: list tests without running them.
- `-R <regex>`: select tests matching a regular expression.
- `-j <n>`: run tests in parallel.
- `--output-on-failure`: print failing output.

The repository also includes `Scripts/run_python_tests.py`, which changes to the RDKit code directory and runs `test_list.py` through RDKit's `TestRunner`. Treat it as a repository test harness that assumes a working RDKit import and configured paths.

## Minimal Test Planning Examples

### Descriptor C++ change

1. Inspect `Code/GraphMol/Descriptors/` CMake targets and changed source files.
2. Build the descriptor-related target or test target.
3. Run `ctest -R 'Descriptor|Descriptors' --output-on-failure` after confirming names with `ctest -N`.
4. Run Python descriptor tests such as `rdkit/Chem/UnitTestDescriptors.py` if Python-visible behavior changes.
5. Add or update tests in the narrowest layer where the behavior lives.

### Python wrapper signature change

1. Inspect the relevant `Code/*/Wrap/CMakeLists.txt` for extension and pytest target names.
2. Build the wrapper extension.
3. Run the wrapper-local Python test.
4. Run one package-level import/API smoke test outside shadowing conditions.
5. Consider generated stubs/docstrings only if public signatures changed and maintainers expect regenerated artifacts.

## Do Not Overstate Validation

- Running a binary-package smoke test does not validate local source edits.
- Running only a Python test does not validate C++ code paths if the test imported the wrong RDKit.
- A successful CMake configure does not validate optional components that were disabled.
- A passing focused test should be described as focused validation, not full repository validation.
