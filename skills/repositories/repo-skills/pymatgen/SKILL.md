---
name: pymatgen
description: "Use pymatgen for computational materials workflows, including
  structures, entries, thermodynamics, external data, surfaces, spectra, CLIs,
  and configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# pymatgen

Use this repo skill when a task mentions pymatgen, computational materials analysis, crystal structures, local environments, Materials Project data, phase-diagram-ready entries, compatibility corrections, batteries, slabs, surfaces, Pourbaix diagrams, diffraction, spectra, `pmg`, `.pmgrc.yaml`, or VASP/POTCAR-related pymatgen workflows.

## Start Here

- Install for normal use with `pip install pymatgen` on Python `>=3.11`; install optional extras only for the workflow that needs them.
- Run `python scripts/check_pymatgen_install.py --help`, then `python scripts/check_pymatgen_install.py` for a redacted import and console-script check.
- Read `references/troubleshooting.md` for cross-cutting install/import, optional dependency, credential, plotting, configuration, and package-split issues.
- Read `references/repo-provenance.md` before deciding whether this skill matches a current checkout or should be refreshed.

## Route by Task

- Use `sub-skills/structures-local-environments-and-transformations/SKILL.md` for `Structure`, `Molecule`, `Lattice`, local neighbors, `CrystalNN`, `VoronoiNN`, `StructureGraph`, dimensionality, Chemenv, prototypes, molecule matching, functional groups, and magnetism.
- Use `sub-skills/entries-thermodynamics-and-batteries/SKILL.md` for `ComputedEntry`, compatibility corrections, GGA/GGA+U or r2SCAN mixing, phase-diagram-ready entries, batteries, voltage profiles, `VaspToComputedEntryDrone`, and `BorgQueen`.
- Use `sub-skills/external-data-access/SKILL.md` for `MPRester`, Materials Project fields, `PMG_MAPI_KEY`, COD, OPTIMADE, credentials, pagination, rate limits, and network-safe query planning.
- Use `sub-skills/surfaces-interfaces-and-electrochemistry/SKILL.md` for slabs, surface energies, Wulff shapes, work functions, substrate matching, coherent interfaces, Pourbaix diagrams, and interfacial reactivity.
- Use `sub-skills/spectra-diffraction-and-visualization/SKILL.md` for XRD/neutron/TEM diffraction, `DiffractionPattern`, XAS, XPS, `SpectrumPlotter`, FEFF plotting expectations, optional VTK/chemview visualization, and headless plotting.
- Use `sub-skills/cli-and-configuration/SKILL.md` for `pmg` subcommands, `get_environment`, FEFF console scripts, `.pmgrc.yaml`, POTCAR/CP2K setup, Materials Project key persistence, and safe CLI help discovery.

## Common Workflow Pattern

1. Identify whether the user is asking for Python APIs, CLI/configuration, live external data, or interpretation of existing materials objects.
2. If live data or credentials are involved, plan offline first and require explicit authorization before network access or secret use.
3. Keep structure construction, entry correction, and analysis interpretation in the owning sub-skill instead of mixing responsibilities.
4. Prefer in-memory examples and bundled scripts for smoke checks; do not require access to the original repository checkout.
5. For plotting or visualization in automation, set a noninteractive backend and save files instead of opening GUI windows.

## Safety Boundaries

- Do not run commands that mutate `.pmgrc.yaml`, generate/copy POTCARs, scan user calculation directories, access Materials Project/COD/OPTIMADE, open GUI windows, or write output files without user approval.
- Do not print API keys, headers, `.pmgrc.yaml` contents, local executable paths, or private calculation-directory names in reusable guidance.
- Treat VASP POTCAR resources as licensed user data; pymatgen can help configure paths or generate POTCAR files only when the user has lawful local resources.
- Treat optional extras such as visualization, symmetry/prototype, matcalc/MLP, ASE, tblite, ABINIT, or zeo++ support as conditional rather than baseline install requirements.

## Bundled Assets

- `scripts/check_pymatgen_install.py` performs a redacted package, import, and console-script check without network access or configuration mutation.
- `references/troubleshooting.md` covers shared install/import, optional dependency, credential, data/config, plotting, and command-safety issues.
- Each sub-skill owns its detailed API/workflow references and safe smoke scripts.
