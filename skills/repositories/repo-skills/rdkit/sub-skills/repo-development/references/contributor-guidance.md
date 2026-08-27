# RDKit Contributor Guidance for Agents

This reference distills repository-facing contributor guidance for agents making source changes. Keep changes minimal, tested, and easy for maintainers to review.

## Contribution Expectations

- Add or update tests for behavior changes.
- Prefer C++ for core toolkit functionality unless the change is specifically Python-only.
- For C++ behavior exposed to Python, consider both C++ and Python-facing coverage.
- Keep bug reports, fixes, and examples reproducible with small molecules or data where possible.
- If AI-generated code materially contributes to a PR, the contributor guidance asks for transparent acknowledgement in the PR description and human review before submission.
- For larger behavior changes, document the rationale and consider whether maintainer discussion is needed before implementing broad API changes.

## Python Style

The repository style configuration is in `setup.cfg` and is used by `Scripts/PythonFormat.py`.

Key Python formatting settings:

- YAPF based on PEP 8.
- Two-space indentation.
- Two-space continuation indentation.
- Maximum line length of 100.
- An extra blank line before nested class or function definitions.
- Avoid short one-line `if` bodies formed by joining multiple lines.

Use the repository style rather than adding a new formatter configuration. A focused file can be formatted with a command shaped like:

```bash
yapf --style setup.cfg --in-place path/to/file.py
```

`Scripts/PythonFormat.py` scans Python files under the repository, excluding build and external directories, and reports diffs plus suggested YAPF commands. It assumes the repository root is available through `RDBASE`.

## Test and Documentation Discipline

- Python tests generally use `UnitTest*.py` names under `rdkit/` or `Projects/`.
- `rdkit/pytest.ini` enables doctests and ignores selected legacy/demo files.
- C++ tests are registered in CMake near the implementation with target names selectable by `ctest -R`.
- Documentation is mostly reStructuredText and may include doctest examples.
- For public API changes, update examples, docs, and tests together when applicable.

## Generated Stubs

The repository includes `Scripts/gen_rdkit_stubs` for Python stub generation. Treat this as a maintainer/reference workflow, not a default step for ordinary code edits.

Important behavior:

- It can be invoked as part of the build by enabling the relevant CMake stub-generation option.
- If run manually, the intended built or installed RDKit modules must be first on `sys.path`.
- The script purges RDKit source directories from `sys.path` to avoid generating stubs from the wrong tree.
- It requires `pybind11_stubgen` to be importable.
- It writes an `rdkit-stubs` directory to the selected output directories.

Manual command shape:

```bash
python -m Scripts.gen_rdkit_stubs --help
```

Only recommend regenerating stubs when public Python signatures or wrapper exposure changed and the maintainer workflow requires it.

## Generated/Patchable Docstrings

The repository includes `Scripts/patch_rdkit_docstrings`, a maintainer script that scans RDKit C++ sources and uses generated stubs plus clang include information to patch docstrings/signatures.

Important behavior:

- It is a runnable Python module.
- It needs RDKit include paths and clang/Python include configuration.
- It has a `--clean` option for removing generated original-docstring backup files.
- It purges source checkout paths before locating import/include data.

Command shape:

```bash
python -m Scripts.patch_rdkit_docstrings --help
```

Do not run or recommend this as a casual formatting step. Use it only for maintainer workflows involving public wrapper docstrings/signatures.

## Maintainer Safety Checklist

Before handing off a repository edit:

- Identify whether the edited behavior is Python-only, C++-only, wrapper-exposed, build-system, docs, data, project, or contrib code.
- Confirm the selected tests actually import or build the edited source rather than a preinstalled binary package.
- Add or update the smallest meaningful test for changed behavior.
- Run focused validation first; widen only as needed for risk.
- Note skipped optional components explicitly instead of implying full coverage.
- Avoid broad cleanup, unrelated formatting, or generated artifact churn unless the task asks for it.
