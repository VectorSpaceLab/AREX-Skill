# RDKit Cross-Cutting Troubleshooting

Use this root troubleshooting page for issues that affect multiple RDKit workflows. For workflow-specific symptoms, continue to the nearest sub-skill troubleshooting reference.

## `ImportError` from a Source Checkout

Symptom: importing `rdkit` from a repository checkout fails with a message like `cannot import name 'rdBase'`.

Likely cause: the local `rdkit/` package directory shadows an installed RDKit package, but compiled extension modules have not been built in the checkout.

Recovery:

1. Run `python scripts/check_rdkit_env.py` from the skill root or run `sub-skills/repo-development/scripts/check_checkout_shadowing.py` for checkout-specific diagnostics.
2. For normal usage, run code from outside the source checkout or install RDKit from conda-forge.
3. For repository development, build the C++/Python wrappers before importing from the checkout and use the `repo-development` sub-skill.

## Missing Compiled Extensions

Symptoms include missing `rdBase`, missing `rdkit.Chem.rdchem`, missing `rdFingerprintGenerator`, or import failures from modules that are normally compiled extensions.

Likely causes:

- source checkout has not been built;
- Python is importing the wrong `rdkit` package;
- Python version or ABI does not match compiled modules;
- optional wrappers were not enabled at build time.

Recovery:

- Inspect `rdkit.__file__` from a neutral directory to confirm which package is imported.
- Prefer a conda-forge binary package for user workflows.
- For source builds, verify CMake options such as `RDK_BUILD_PYTHON_WRAPPERS`, build directory, and Python interpreter alignment.

## Invalid Molecules Propagating Downstream

Symptoms include descriptor errors, reaction failures, conformer embedding exceptions, drawing crashes, or `NoneType` failures after parsing SMILES/SDF input.

Recovery:

- Validate every molecule from `Chem.MolFromSmiles`, `Chem.MolFromMolBlock`, suppliers, or reaction products before downstream use.
- Keep invalid rows with input identifiers so the user can correct source data.
- Route parsing and sanitization questions to `sub-skills/molecule-io-core/`.

## Optional Dependencies and Build Options

RDKit has many optional surfaces: InChI, Avalon, CoordGen, FreeSASA, PostgreSQL cartridge, ChemDraw/MAE parsers, PubChem shape, MinimalLib/CFFI/SWIG wrappers, pandas, database helpers, and Contrib utilities.

Recovery:

- Check availability with imports or feature-specific API calls before promising a workflow.
- If an optional wrapper is unavailable, explain the missing build option or dependency rather than treating it as a core RDKit failure.
- Route Contrib and database/pandas/data-file issues to the relevant sub-skill.

## RDKit Data Files Missing

Symptoms include failure to find `BaseFeatures.fdef`, PAINS definitions, salts, fragment descriptor CSVs, or sample database files.

Recovery:

- Use `rdkit.RDConfig.RDDataDir` and check that the expected file exists.
- Avoid hard-coded install paths.
- Route feature-definition and data-file tasks to `sub-skills/data-cli-integration/`.

## Deprecated or Changed APIs

RDKit evolves quickly; older helper APIs can emit deprecation warnings while still working. For example, modern fingerprint workflows should prefer `rdkit.Chem.rdFingerprintGenerator` over older Morgan helper calls when building new code.

Recovery:

- Prefer generator APIs and current docs when writing new code.
- Preserve old behavior only when maintaining legacy code or matching existing tests.
- Record version-sensitive behavior in code comments or tests when a user asks for compatibility.
