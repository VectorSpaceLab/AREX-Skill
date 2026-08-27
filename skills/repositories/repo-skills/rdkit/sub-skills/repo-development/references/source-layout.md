# RDKit Source Layout for Repository Work

This reference helps agents decide where a repository change belongs and which adjacent tests or build files to inspect. It is for editing RDKit itself, not for ordinary package usage.

## Top-Level Map

- `CMakeLists.txt`: top-level project configuration, feature flags, build outputs, compiler standards, dependency discovery, and version metadata.
- `Code/`: main C++ libraries, headers, wrapper modules, C++ tests, and most CMake targets.
- `rdkit/`: Python package tree, Python tests, doctest-enabled modules, Python package CMake integration, and `RDPaths.py` generation.
- `Data/`: runtime data files used by installed RDKit features.
- `Docs/`: user and developer documentation, mostly reStructuredText plus generated API documentation support.
- `Scripts/`: repository maintenance helpers, test runner, formatting checker, generated-stub tooling, docstring patching, and release/development scripts.
- `Projects/DbCLI`: project-level Python package/tests for database command-line workflows.
- `Contrib/`: optional contributed utilities that may have their own expectations and dependencies.
- CI configuration: useful as evidence for expected jobs, but do not treat CI-specific paths or secrets as runtime dependencies.

## C++ Library and Wrapper Boundaries

Most compiled implementation lives under `Code/`. Common patterns:

- `Code/<area>/CMakeLists.txt` declares core libraries, headers, and tests with RDKit CMake helpers.
- `Code/<area>/Wrap/` contains Python extension wrappers for the area when exposed to Python.
- C++ tests are commonly registered with `rdkit_test(...)` and are selectable through `ctest -R <name>` after a build.
- Python wrapper tests are commonly registered with `add_pytest(...)` and usually live near the wrapper source as `test*.py` or `rough_test.py`.

Examples of source-to-wrapper relationships:

- `Code/RDBoost/Wrap/` builds the foundational `rdBase` Python extension.
- `Code/DataStructs/Wrap/` exposes DataStructs extension modules such as bit-vector support.
- `Code/GraphMol/Fingerprints/Wrap/` exposes fingerprint generator modules.
- `Code/GraphMol/MolStandardize/Wrap/` exposes MolStandardize behavior to Python.
- `Code/GraphMol/MolDraw2D/Wrap/` exposes drawing behavior.

When changing C++ behavior that is exposed to Python, inspect both the core C++ target and the wrapper/Python test target.

## Python Package Tree

The `rdkit/` directory is the import package and also contains many Python tests. It is not a complete standalone pure-Python package when the checkout is unbuilt: compiled extension modules must come from a build or install.

Important files and conventions:

- `rdkit/CMakeLists.txt` writes `RDPaths.py`, selects source-vs-installed test locations, and registers package-level Python pytest handling.
- `rdkit/pytest.ini` sets `python_files = UnitTest*.py`, enables doctests, and lists package-level ignore rules.
- Python unit tests are usually named `UnitTest*.py`.
- `Projects/pytest.ini` uses the same `UnitTest*.py` convention for project tests.

## Test Discovery Clues

Use filenames and CMake target names together:

- For Python-only changes under `rdkit/Chem/Descriptors.py`, start with nearby `rdkit/Chem/UnitTestDescriptors.py` and relevant doctests.
- For C++ descriptor changes under `Code/GraphMol/Descriptors/`, inspect CMake targets in that directory and Python tests that consume descriptors.
- For wrapper changes under `Code/*/Wrap/`, run the wrapper-specific `add_pytest` target or the source test file directly where possible.
- For package-wide Python behavior, use `python -m pytest` from the package test root only after import shadowing is resolved.
- For database command-line work, inspect `Projects/DbCLI/UnitTestDbCLI.py` and `Projects/pytest.ini`.

## Data, Docs, Projects, and Contrib

- Data changes should be paired with tests that load the data through RDKit APIs, not only file-presence checks.
- Docs changes should preserve reStructuredText conventions and doctest examples when present.
- `Projects/DbCLI` has project-specific tests and may depend on database-related optional behavior.
- `Contrib/` contains optional utilities; avoid applying core-package assumptions blindly. Check local README/test files before editing.

## Maintainer Safety

- Do not assume an import from a source checkout validates the checkout. It may be importing source Python files while missing compiled extensions.
- Do not rely on a binary package to validate modified C++ source. Binary imports only prove installed package behavior, not local source changes.
- Do not link runtime skill instructions to local source paths. Copy or distill any reusable workflow into the skill itself.
