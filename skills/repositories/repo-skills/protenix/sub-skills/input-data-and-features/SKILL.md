---
name: input-data-and-features
description: "Author, validate, and convert Protenix input JSON for proteins,
  nucleic acids, ligands, ions, paths, bonds, and constraints without running
  inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Input Data and Features

Use this sub-skill when a task is about preparing Protenix input before prediction: authoring JSON jobs, validating entity blocks, choosing ligand encodings, checking MSA/template path fields, defining covalent bonds or constraints, or planning structure-to-JSON conversion.

## Use This For

- Build the top-level list-of-jobs JSON with `name`, `sequences`, optional `covalent_bonds`, optional `constraint`, and optional `modelSeeds`.
- Author `proteinChain`, `dnaSequence`, `rnaSequence`, `ligand`, and `ion` entries with correct `count`, optional `id`, modifications, and sequence alphabets.
- Fill existing `pairedMsaPath`, `unpairedMsaPath`, and `templatesPath` fields without running MSA/template searches.
- Encode ligand `CCD_`, `SMILES`, and `FILE_` forms, bare-code ions, polymer-ligand bonds, ligand-ligand bonds, contact constraints, and pocket constraints.
- Plan `protenix json` conversion from PDB/mmCIF/CIF or use conversion API signatures when an installed Protenix environment is available.

## Route Elsewhere

- Run prediction, choose model variants, tune inference flags, or interpret output confidence files with `../cli-and-inference/SKILL.md`.
- Generate missing protein MSA, template, or RNA MSA files with `../msa-template-and-prep/SKILL.md`.
- Prepare training datasets, bioassembly caches, or training-time data schemas with `../training-and-data-pipeline/SKILL.md`.

## Start Here

1. Read `references/input-json-schema.md` for accepted job/entity/path/bond/constraint shapes and copyable snippets.
2. Run `python scripts/validate_protenix_input_json.py scripts/protenix_minimal_input.json` for a validator smoke test.
3. Run `python scripts/validate_protenix_input_json.py INPUT.json --check-paths` before handing authored JSON to prediction or preprocessing.
4. Read `references/conversion-and-features.md` for `protenix json`, `cif_to_input_json`, and feature-conversion behavior.
5. Read `references/troubleshooting.md` when JSON is rejected, paths are missing, chemistry parsing fails, or conversion output looks surprising.

## Critical Reminders

- The top-level JSON value is always a list, even for one job.
- Entity numbers in bonds and constraints are 1-based positions in `sequences`, not chain IDs.
- Ligand values use `CCD_`, `FILE_`, or SMILES; ion values use bare codes such as `MG` or `ZN`.
- `pairedMsaPath`, `unpairedMsaPath`, and `templatesPath` should point to existing files, preferably by absolute path.
- `protenix json` converts structures to input JSON; it does not run prediction or generate missing MSA/template files.
