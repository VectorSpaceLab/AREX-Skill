# Troubleshooting RDKit Repository Development

Use this guide when a source checkout, build, or focused test behaves differently from a binary RDKit install.

## `cannot import name rdBase`

Likely cause: Python is importing the repository's `rdkit/` package directory from an unbuilt checkout, but the compiled `rdBase` extension has not been built or is not located where that checkout expects it.

Triage:

1. Run `python scripts/check_checkout_shadowing.py --json` from this sub-skill.
2. Check whether `rdkit.__file__` points into a source checkout instead of a site-packages install or built tree.
3. If using binary RDKit for API inspection, run Python outside the repository checkout or remove the checkout root from `PYTHONPATH`.
4. If validating local source edits, build the relevant CMake targets so extension modules such as `rdBase` exist for the checkout.
5. Do not fix this by editing `rdkit/__init__.py`; fix the import context or build state.

Important distinction: binary imports working outside the checkout prove the installed package is usable; they do not prove local source edits are built or tested.

## Unbuilt Extension Modules

Symptoms:

- Importing `rdkit` partially works but importing `rdBase`, `Chem`, `DataStructs`, or wrapper modules fails.
- Python tests fail immediately before exercising the changed source.
- `rdkit.__file__` points to source files while `.so`, `.pyd`, or platform extension modules are absent.

Actions:

- Build RDKit with Python wrappers enabled.
- Ensure the build/install output is first on the runtime import path when validating local edits.
- Avoid running package tests from a checkout that shadows the installed package unless the checkout has been built.
- Use CTest target names when validating compiled code instead of relying only on direct Python imports.

## CMake Dependency or Configure Failures

Symptoms:

- Configure fails before compiling RDKit code.
- Optional feature checks fail for InChI, Avalon, PostgreSQL, FreeSASA, CoordGen, MAE parser, PubChemShape, Qt, Java/SWIG, CFFI, or fuzz targets.
- Network-restricted builds fail while fetching or discovering dependencies.

Actions:

- Decide whether the failed optional component is relevant to the change.
- Disable unrelated optional components rather than debugging them as source failures.
- Keep Python wrappers enabled for Python-facing changes.
- Verify configure and at least one representative build/test target before claiming a build-system change is safe.
- Record skipped optional components in the handoff.

## Local Checkout Shadows Binary Package

A common workflow is to install RDKit from a binary package for API inspection while also keeping the source checkout open. If Python starts inside the checkout, the local `rdkit/` directory can take priority over site-packages.

Signs:

- `sys.path[0]` is the repository root or a subdirectory that exposes the checkout.
- `rdkit.__file__` points to a local `rdkit/__init__.py`.
- `from rdkit import rdBase` fails inside the checkout but works from another directory.

Fixes:

- For binary API checks, change to a neutral directory before running Python.
- For source validation, build the checkout and use the build/install output intentionally.
- Remove repository paths from `PYTHONPATH` when not validating local source.
- Use the bundled checker with `--expect-binary` when an installed package should be used.

## Generated Stub or Docstring Problems

Stub generation issues:

- `pybind11_stubgen` missing: install or activate the maintainer environment that provides it.
- Stubs generated for the wrong RDKit: ensure the intended RDKit modules are first on `sys.path` and avoid source-checkout shadowing.
- Stubs missing compiled modules: build/install the target modules first.

Docstring patching issues:

- Missing clang include paths or Python include paths: provide the required script arguments or environment configuration.
- Missing RDKit include path: build/install or pass `--rdkit-include-path`.
- Unexpected source edits: inspect generated backups and use script options such as `--clean` only in a maintainer workflow.

Do not bundle generated stubs or patched docstrings into unrelated changes unless public signatures or wrapper docstrings intentionally changed.

## Focused Tests Miss the Change

Symptoms:

- A Python test passes but the edited C++ code was not rebuilt.
- CTest passes a nearby target but the Python wrapper behavior changed without a Python-facing test.
- A descriptor or fingerprint change passes one test file but fails in broader public API usage.

Actions:

- Trace the changed file to its CMake target and package import path.
- Run both C++ and Python-facing tests for wrapper-exposed behavior.
- Add a regression test in the layer where the bug was observed.
- Use `ctest -N -R <regex>` to ensure the intended tests are selected.
- Widen from local tests to area tests before final handoff when behavior crosses module boundaries.

## When Not to Change Source

Do not edit RDKit source until the environment issue is ruled out if:

- The only symptom is `rdBase` missing from an unbuilt checkout.
- The failure disappears outside the checkout using the same installed package.
- CMake optional dependency failures are unrelated to the requested code area.
- A generated-stub/docstring workflow is failing because prerequisites are missing.
