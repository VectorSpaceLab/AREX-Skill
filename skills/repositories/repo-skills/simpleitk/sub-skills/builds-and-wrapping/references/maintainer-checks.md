# Maintainer Checks and Safe Validation

This page separates read-only checks from expensive or mutating maintainer actions.

## Safe Read-Only Checks

These are appropriate before suggesting a build or while answering a build-system question:

```bash
python skills/disco/simpleitk/sub-skills/builds-and-wrapping/scripts/check_build_metadata.py /path/to/SimpleITK
python - <<'PY'
import SimpleITK as sitk
print(sitk.Version())
print(hasattr(sitk, "ElastixImageFilter"), hasattr(sitk, "TransformixImageFilter"))
PY
```

The bundled metadata helper reads only expected source files and prints JSON. It does not configure CMake, install packages, download dependencies, modify generated files, or inspect private environments.

For ImageIO discovery in runtime checks, use object APIs:

```python
import SimpleITK as sitk
reader_ios = sitk.ImageFileReader().GetRegisteredImageIOs()
writer_ios = sitk.ImageFileWriter().GetRegisteredImageIOs()
```

Do not use a module-level `sitk.GetRegisteredImageIOs()`; that was not present in the inspected wheel.

## Build Metadata To Inspect

- `pyproject.toml`: Python build backend, scikit-build settings, package name, Python requirement, CMake defines.
- `Version.cmake`: checkout development version components.
- `CMakeLists.txt`: top-level options such as `SimpleITK_USE_ELASTIX`, `BUILD_SHARED_LIBS`, and `SimpleITK_INT64_PIXELIDS`.
- `CMake/sitkLanguageOptions.cmake`: language wrapper discovery and `WRAP_*` options.
- `Wrapping/CMakeLists.txt`: which wrapper subdirectories are included.
- `Wrapping/Python/CMakeLists.txt`: Python/SWIG/limited-API behavior.
- `SuperBuild/*.cmake`: external dependency strategy for ITK, SWIG, PCRE2, GTest, elastix, and examples.
- `.pre-commit-config.yaml`: local contributor checks.
- `.readthedocs.yml`: documentation build environment and requirements entry point.

## Pre-Commit Checks

The checkout uses pre-commit hooks for general hygiene and repository-specific checks. Relevant hook families include:

- Secret/key and platform filename checks.
- JSON, YAML, XML, whitespace, and EOF checks.
- `black` for Python formatting.
- `clang-format` for C/C++ headers and source.
- `gersemi` for CMake formatting.
- JSON schema validation for filter description YAML.
- Comment spell checking.
- Local hooks around development setup and commit metadata.

Running the entire pre-commit suite may install hook environments and run formatters, so treat it as mutating unless invoked in check-only mode and the user approves. For focused review, prefer reading `.pre-commit-config.yaml` and running the smallest relevant check.

## Tests

SimpleITK tests are CTest-based after a configured build. The docs recommend enabling `BUILD_TESTING` and then running CTest from the inner build tree:

```bash
ctest .
ctest -C Release
```

Guidance:

- Treat full `ctest` as expensive; it can cover many language wrappers and examples.
- Prefer a targeted `ctest -R <pattern>` when investigating one wrapper or build option.
- Native tests may require ExternalData downloads; missing HTTPS support in CMake can cause data download failures.
- Do not run build-tree tests before a successful configure/build.

## Docs Build

Documentation is Sphinx-based. The readthedocs config uses:

- Sphinx configuration: `docs/source/conf.py`.
- Requirements file: `docs/requirements.txt`.
- Python tool version: documented as Python 3.12 in `.readthedocs.yml`.

Local docs build pattern from the docs:

```bash
python -m venv sitkenv
. sitkenv/bin/activate
python -m pip install -r SimpleITK/docs/requirements.txt
make -C SimpleITK/docs html
```

This creates an environment and installs packages, so do not run it as a passive verification step. For documentation edits, first check whether the task actually changes docs and whether a smaller syntax/read check is enough.

## Development Setup Script

`Utilities/SetupForDevelopment.sh` configures git remotes, GitHub references, pre-commit, local git config, legacy hook migration, and a setup version marker. It is reference-only for this skill because it mutates developer state. Do not bundle or run it as a runtime helper.

## JSON and Generation Utilities

SimpleITK has generation and JSON/schema utilities for filters and wrappers. Treat them as source evidence unless a specific maintainer task asks for regeneration. They can modify generated files or require repository-specific build context, so they are not bundled into this runtime skill.

## Release-Heavy Exclusions

The following are outside this sub-skill unless the user explicitly asks for release engineering:

- Release artifact upload/download automation.
- Download statistics scripts.
- Official distribution signing or publication.
- Cross-platform release matrix orchestration.
- Hand-editing generated wrapper outputs instead of changing sources/templates.

## Safe Maintainer Triage Flow

1. Read the user’s exact goal and classify it as binary install, Python source build, full SuperBuild, direct CMake, wrapper dependency, docs, tests, or release work.
2. Run read-only metadata inspection if the source tree is available.
3. State whether the next command is safe/read-only, expensive, or mutating.
4. For builds, ask for approval or constraints before starting downloads, environment creation, or multi-hour compilation.
5. Prefer narrow validation commands: metadata helper, import/version check, `hasattr` for optional APIs, targeted `ctest -R`, or focused docs build.
6. Record skipped heavyweight checks honestly instead of implying they passed.
