---
name: repo-development
description: "Safely edit, build, and test the RDKit repository itself,
  including CMake/Python wrapper boundaries, focused tests, formatting,
  generated stubs/docstrings, and checkout-shadowing diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# RDKit Repository Development

Use this sub-skill when a request is about changing RDKit source code, diagnosing a local checkout, selecting maintainer tests, adjusting build configuration, or preparing a contribution to RDKit itself.

## Route Here

- Edit C++ core code under `Code/`, Python package code under `rdkit/`, build files, wrappers, tests, or maintainer scripts.
- Decide whether a change needs C++ tests, Python wrapper tests, doctests, CMake updates, docs, or generated artifacts.
- Diagnose import failures caused by an unbuilt checkout shadowing an installed RDKit package, especially missing `rdBase`.
- Choose focused `ctest`, `pytest`, or script-based test commands after a source change.
- Check repository formatting expectations from `setup.cfg` and maintainer scripts.
- Understand generated Python stubs or docstring patching workflows as maintainer-only reference workflows.

## Route Elsewhere

- Use `../molecule-io-core/` for ordinary SMILES, SDF, sanitization, canonicalization, and molecule-validation usage.
- Use `../descriptors-fingerprints/` for descriptor, fingerprint, similarity, clustering, or ML feature tasks.
- Use `../conformers-drawing/` for conformer generation, alignment, shape, drawing, or visualization usage.
- Use `../reactions-standardization/` for reaction handling, salt/fragment/charge cleanup, tautomer enumeration, or MolStandardize workflows.
- Keep end-user package examples out of this sub-skill unless they are tests for repository changes.

## Start With These References

- `references/source-layout.md` maps RDKit source areas, Python package boundaries, wrappers, tests, data, docs, projects, and contrib code.
- `references/build-and-test.md` covers CMake build caveats, conda/binary-vs-source import hazards, and focused test selection.
- `references/contributor-guidance.md` summarizes style, test expectations, documentation expectations, and generated stub/docstring workflows.
- `references/troubleshooting.md` diagnoses `rdBase` import failures, unbuilt extension modules, dependency/configure failures, generated artifacts, and test misses.
- `scripts/check_checkout_shadowing.py` checks whether the current directory is shadowing an installed RDKit or lacks the compiled `rdBase` extension.

## Safe Development Defaults

- Treat RDKit as a compiled C++/Python project: many Python imports depend on extension modules produced by the CMake build, not just files under `rdkit/`.
- Run repository imports from a built tree, installed tree, or outside the checkout when using a binary package; an unbuilt checkout can mask the installed package and fail at `rdBase`.
- Prefer focused tests near the touched module first, then widen to relevant `ctest -R` or `pytest` suites before claiming a change is safe.
- For Python formatting, follow the repository YAPF settings: two-space indentation and 100-character line limit from `setup.cfg`.
- For C++ changes exposed to Python, update both the C++ tests and wrapper/Python tests when behavior crosses that boundary.

## Quick Diagnostics

From any working directory, run the bundled checker:

```bash
python scripts/check_checkout_shadowing.py
```

Typical outcomes:

- `OK`: RDKit imports and `rdBase` is available from the same import root.
- `SHADOWING`: Python is loading a source checkout that appears to lack built extension modules.
- `IMPORT_ERROR`: RDKit import fails before the checker can confirm `rdBase`; inspect the reported exception and `sys.path` hint.

Use `--json` for machine-readable output when another agent needs to branch on the result.

## Maintainer Workflow Pattern

1. Map touched files to source ownership using `references/source-layout.md`.
2. Decide whether the change is Python-only, C++-only, C++ plus wrapper, CMake/build-system, docs/data, or contrib/project code.
3. Use `references/build-and-test.md` to select the smallest meaningful tests and add a widening test if behavior crosses module boundaries.
4. Use `references/contributor-guidance.md` for style, documentation, and generated-artifact guidance.
5. If imports fail from a checkout, run `scripts/check_checkout_shadowing.py` and apply `references/troubleshooting.md` before changing source code.
