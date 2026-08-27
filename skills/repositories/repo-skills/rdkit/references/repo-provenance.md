# RDKit Repo Provenance

schema: `disco.repo-provenance.v1`

This file is the refresh baseline for the generated `rdkit` skill.

## Source Snapshot

- VCS: Git
- Commit: `73ef78025c9a265e42b8c9578775de18b11f1829`
- Branch: `master`
- Exact tag: none detected
- Remote URL: https://github.com/rdkit/rdkit
- Source version variables from `CMakeLists.txt`: `RDKit_Year=2026`, `RDKit_Month=09`, `RDKit_Revision=1`, `RDKit_RevisionModifier=pre`, `RDKit_ABI=1`
- Working tree state at generation: dirty because new DisCo output was created under `skills/`

## Inspection Package Facts

- Installed distribution inspected for live API facts: `rdkit`
- Inspection package version: `2026.03.3`
- Verified import modules: `rdkit`, `rdkit.Chem`, `rdkit.DataStructs`, `rdkit.Chem.AllChem`, `rdkit.Chem.rdFingerprintGenerator`, `rdkit.Chem.MolStandardize`, `rdkit.ML.Cluster.Butina`
- Verification result: import checks, distribution metadata, `pip check`, and a core molecule/descriptor/fingerprint compiled-extension smoke passed
- Important caveat: the source checkout is a mixed C++/Python tree; importing from an unbuilt checkout can shadow an installed package and fail before compiled modules such as `rdBase` are available

## Evidence Paths

Primary evidence used to generate this skill:

- `README.md`, `INSTALL`, `ReleaseNotes.md`, `license.txt`
- `setup.cfg`, `CMakeLists.txt`, `Code/cmake/Modules/RDKitUtils.cmake`, `build_support/pkg_version.py`
- `rdkit/`, especially `rdkit/Chem/`, `rdkit/DataStructs/`, `rdkit/ML/`, `rdkit/RDConfig.py`, `rdkit/RDLogger.py`
- `Code/GraphMol`, `Code/DataStructs`, `Code/DistGeom`, `Code/ForceField`, `Code/ChemicalFeatures`, `Code/RDGeneral`, `Code/MinimalLib`
- `Docs/Book`, `Docs/Code`, `Docs/Notebooks`
- `Data/`
- selected `Contrib/` utilities and readmes
- `Projects/DbCLI`
- selected `Scripts/` helpers
- selected tests and notebooks under `rdkit/`, `Docs/Notebooks/`, `Contrib/`, and `Projects/DbCLI`

## Excluded or De-Prioritized Evidence

- `.git/`, CI metadata, generated/build/cache outputs
- vendored third-party internals under `External/`
- benchmarks, fuzzers, broad regression timing scripts, and long-running tests except as evidence for skip decisions
- secondary Java/C#/web wrapper surfaces unless needed for routing
- duplicate translated docs under `Docs/Book_jp`
- `skills/tests/`, which is the DisCo review/test artifact area rather than runtime skill content

## Refresh Guidance

Refresh this skill when RDKit source APIs, docs, examples, CMake options, Contrib layouts, data-file conventions, package version, or generated wrapper behavior change. Compare this provenance against the current checkout before assuming the skill is aligned with a later RDKit tree.
