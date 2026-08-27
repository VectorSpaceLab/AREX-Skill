# Troubleshooting Contrib Utilities

Use this guide when optional RDKit Contrib tools fail in an environment where core `rdkit` imports work.

## Core RDKit Imports but Contrib Module Missing

Symptom examples:

- `ModuleNotFoundError: No module named 'sascorer'`
- `ModuleNotFoundError: No module named 'npscorer'`
- `ModuleNotFoundError: No module named 'freewilson'`

Cause:

- Core RDKit binary packages can install `rdkit` without installing every source-tree `Contrib` script as an importable top-level Python module.

Response:

1. Confirm core RDKit works with `from rdkit import Chem`.
2. Check the specific contrib module with `importlib.util.find_spec()` or a guarded import.
3. Ask the user for an installed contrib package/module location, a source distribution that includes the required utility, or permission to install optional extras.
4. Do not hard-code a local source checkout path into generated public code.
5. If the requested task is actually a core descriptor, standardization, or fingerprint task, route to the neighboring core sub-skill.

## Scorer Module Imports but Data Missing

Symptom examples:

- SA Score import succeeds but `calculateScore()` fails looking for `fpscores.pkl.gz`.
- NP Score import succeeds but `readNPModel()` fails looking for `publicnp.model.gz`.

Cause:

- The scorer code depends on data/model files next to the module or passed explicitly.

Response:

- Report the scorer as unavailable until the required data file is present.
- Prefer an explicit data path supplied by the user over implicit current-directory behavior.
- Do not embed large model data in a small smoke script.
- Use `scripts/contrib_scores_smoke.py` to distinguish module absence from data absence.

## Path Assumptions and Current Working Directory

Many contributed scripts were written as source-tree utilities and may assume:

- Data files live next to the script.
- Commands are run from the script directory.
- Input is passed through stdin and output through stdout.
- Helper modules are importable because the current directory is on `PYTHONPATH`.

Response:

- Run scripts from the directory containing their required data files when using a source tree.
- Pass explicit file paths where the script supports them.
- Capture stdout/stderr and output files separately.
- For reusable automation, wrap scripts with explicit path validation rather than relying on the user’s shell location.

## Optional Dependency Failures

NIBR filters:

- Requires pandas and numpy in addition to RDKit.
- Requires the filter CSV shipped with the script.
- Fails if the input CSV lacks the configured SMILES column.

FreeWilson:

- May require scientific Python packages in addition to RDKit.
- Requires aligned analogs, a chemically meaningful scaffold, and numeric regression-ready scores.
- Enumeration can become large without filters.

MMPA and Fraggle:

- MMPA database search may require SQLite/database/indexing support.
- SMARTS database searches can be slow for broad patterns.
- Fraggle’s Python Tversky search can be slow for large libraries.

Response:

- Install only the optional dependency set needed for the selected contrib workflow.
- Start with tiny fixtures before running large libraries.
- Add `--help` checks for CLI-like scripts before assuming command syntax.

## Invalid Molecules and Input Hygiene

Common issues:

- Invalid SMILES parse as `None`.
- MMPA input contains salts, mixtures, or wildcard atoms.
- Activity values for FreeWilson use raw IC50 instead of pIC50-like values.
- NIBR filter input has missing or malformed SMILES strings.

Response:

- Validate molecules in `../molecule-io-core/` before contrib processing.
- Canonicalize MMPA input and remove salts/mixtures before fragmentation.
- Preserve molecule IDs across input and output files.
- Report per-record failures rather than dropping rows silently.

## Core vs Contrib Route Mistakes

Route to `../descriptors-fingerprints/` when the user asks for:

- Morgan/RDKit/atom-pair/topological-torsion fingerprints.
- Tanimoto/Dice/cosine similarity.
- QED, LogP, TPSA, Lipinski, exact molecular weight, descriptor tables, or clustering.

Route to `../reactions-standardization/` when the user asks for:

- `rdMolStandardize` cleanup, normalization, uncharging, fragment/charge parent, or tautomer canonicalization.
- Reaction SMARTS/RXN execution.
- R-group decomposition as a core API workflow.

Stay in `contrib-utilities` when the user explicitly asks for:

- SA Score, NP Score, NIBR filters, Fraggle, contributed MMPA scripts, FreeWilson, or a legacy MolVS contributed utility.

## Smoke Check Interpretation

`scripts/contrib_scores_smoke.py` should be considered successful if:

- RDKit imports.
- All provided SMILES parse successfully.
- The script clearly reports scorer availability or unavailability.

It is acceptable for SA Score or NP Score to be reported unavailable in a binary-only environment. That result confirms the agent should ask for contrib scorer/data installation before scoring rather than inventing values.
