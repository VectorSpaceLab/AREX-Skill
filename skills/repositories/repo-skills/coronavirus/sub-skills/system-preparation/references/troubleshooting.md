# System-preparation troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `No module named openmm` or legacy `simtk` import failure | OpenMM is absent or an old script is being run | Install/verify the supported OpenMM package in the intended environment; use the bundled modern-import helpers and run `check_openmm_env.py`. Do not expose or depend on a private environment path. |
| Force-field XML or residue-template error | Missing optional force field, unmatched residue, or malformed input | Inspect residue names, chain selection, and installed XML resources. Stop on unmatched chemistry; do not guess a template. |
| PDB atom count differs from positions | Corrupt or manually edited structure | Revalidate with structure-curation, preserve topology/positions together, and regenerate the PDB rather than padding arrays. |
| `addSolvent` fails or PME has no box | Non-periodic/incomplete topology, unsupported solvent model, or invalid padding/ion units | Confirm a protein-only topology, use explicit OpenMM units, and inspect the box after `addSolvent`. |
| XML deserialization or `Context` mismatch | System, state, PDB, and integrator came from different runs | Treat the artifact bundle as atomic. Re-run from a matching set and record provenance; do not mix XML by filename alone. |
| `setPositions`/`step` API error | Wrong object type, missing positions, or invalid argument units | Check the API contract in `api-reference.md`; use `unit` quantities and set positions before minimization. |
| Energy is NaN or explodes during the first steps | Clashes, bad ligand parameters, bad protonation, or unstable timestep/mass combination | Stop, inspect the minimized structure and ligand topology, lower timestep, and validate chemistry. Do not hide NaNs by continuing. |
| 4–5 fs continuation is unstable | Constraints or hydrogen mass are incompatible with the timestep, or the system was not equilibrated | Return to a 2 fs baseline, verify mass/constraints, test a tiny run, and report the limitation. |
| CUDA listed but context creation fails with `CUDA_ERROR_UNSUPPORTED_PTX_VERSION` | Driver/toolkit does not support the generated PTX | Use CPU for required checks; diagnose compatible CUDA driver/toolkit separately. Platform enumeration alone is not verification. |
| Output exists or is unexpectedly huge | Accidental overwrite or unbounded historical iteration settings | Use a new output directory, inspect `steps × iterations`, and pass `--allow-long-run` only after explicit review. |
| Complex preparation lacks a ligand template | OpenFF/SystemGenerator/ParmEd or a compatible force-field toolkit is missing or misconfigured | Record the optional dependency block and stop. Never simulate a ligand as an unparameterized protein residue. |
| Result is called “validated” because a smoke test passed | Mechanical success was confused with scientific validation | Report the exact smoke scope, energies/warnings, and unresolved provenance; a short CPU run is not sampling or efficacy evidence. |
