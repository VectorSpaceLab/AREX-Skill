# pymatgen Cross-Cutting Troubleshooting

## When To Read

Read this before debugging install/import failures, optional dependency surprises, Materials Project credentials, configuration mutation, headless plotting, or confusing behavior from the `pymatgen` / `pymatgen-core` package split. Workflow-specific failures live in the nearest sub-skill reference.

## Install And Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'pymatgen'`.
- Core objects import from unexpected modules.
- API examples copied from old code fail at root-level imports.

Likely causes and recovery:

- Use Python `>=3.11` and install with `pip install pymatgen` unless the user is intentionally working on a checkout.
- Current pymatgen depends on `pymatgen-core`; object implementation modules may report `pymatgen.core.*`. That is expected for core objects and compatibility-backed modules.
- Prefer explicit public imports, such as `from pymatgen.core import Structure, Lattice` and `from pymatgen.ext.matproj import MPRester`.
- Run `python scripts/check_pymatgen_install.py` to verify distribution metadata, core imports, and console-script discovery without exposing local paths.

## Optional Dependencies And Extras

Symptoms:

- Visualization imports fail for VTK or chemview.
- Prototype, symmetry, ASE, matcalc, MLP, ABINIT, tblite, or zeo++ workflows fail only when invoked.
- A workflow works in docs but fails in a minimal install.

Recovery:

- Treat optional extras as workflow-specific. Install only the extra needed for the task rather than a broad optional set.
- Route visualization and headless plotting issues to `sub-skills/spectra-diffraction-and-visualization/SKILL.md`.
- Route prototype, Chemenv, structure, and local-environment optional backend issues to `sub-skills/structures-local-environments-and-transformations/SKILL.md`.
- If a task needs external binaries such as VASP, FEFF, enumlib, bader, Voro++, or Zeo++, stop and ask the user to confirm availability and licensing.

## Credentials, Network, And External Data

Symptoms:

- `MPRester` fails with authentication, endpoint, field-name, rate-limit, or network errors.
- COD or OPTIMADE requests time out or return provider-specific failures.
- A user asks to save or print API keys.

Recovery:

- Plan queries offline first. Do not make Materials Project, COD, or OPTIMADE calls unless the user authorizes network access and confirms any credentials.
- Never echo API keys or secret-bearing headers. Validate only presence and shape when needed.
- Use `sub-skills/external-data-access/SKILL.md` for provider-specific query planning, field selection, and pagination.
- Use `sub-skills/cli-and-configuration/SKILL.md` only when the user wants persistent configuration such as saving `PMG_MAPI_KEY`.

## Configuration And Licensed Data

Symptoms:

- `pmg config` would mutate `.pmgrc.yaml`.
- POTCAR generation fails or asks for pseudopotential paths.
- CP2K data conversion writes generated resources.

Recovery:

- Treat configuration mutation as opt-in. Ask before running `pmg config --add`, `pmg config --potcar`, `pmg config --cp2k`, or installation helpers.
- VASP POTCAR files are licensed user-provided data. Do not download, create, or copy them unless the user provides lawful local inputs and approves the action.
- Prefer reading `sub-skills/cli-and-configuration/references/configuration.md` before changing persistent settings.

## Data And Scientific Provenance

Symptoms:

- Compatibility correction filters entries unexpectedly.
- Surface or Pourbaix results look unphysical.
- Diffraction or local-environment results disagree between methods.

Recovery:

- Preserve provenance before analysis: energy units, calculation method, `run_type`, `hubbards`, POTCAR metadata, oxidation states, structure/site ordering, and data source.
- Route entry corrections and batteries to `sub-skills/entries-thermodynamics-and-batteries/SKILL.md`.
- Route surface, Pourbaix, and interface energy provenance to `sub-skills/surfaces-interfaces-and-electrochemistry/SKILL.md`.
- Route local-environment disagreements to `sub-skills/structures-local-environments-and-transformations/SKILL.md`.

## Headless Plotting And GUI Boundaries

Symptoms:

- Plotting hangs, opens a GUI, or fails with backend/display errors.
- `pmg view` or visualization imports fail in a remote terminal.

Recovery:

- Prefer API workflows that set a noninteractive matplotlib backend and save plots to files.
- Avoid `pmg view`, VTK, and chemview workflows unless the user confirms an interactive-capable environment.
- Route plotting APIs to `sub-skills/spectra-diffraction-and-visualization/SKILL.md`; route CLI plotting flags to `sub-skills/cli-and-configuration/SKILL.md`.
