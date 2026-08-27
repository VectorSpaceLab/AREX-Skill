---
name: structure-curation
description: "Validate and curate coronavirus PDB structures, chains, residues,
  and ligand naming before OpenMM preparation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: CC BY 4.0
---

# Structure curation

Use this route before simulation when a PDB must be inspected, restricted to chains or residue ranges, truncated to a domain, or normalized for a ligand/residue handoff. The bundled helpers are conservative: they report selections, require explicit outputs, and fail rather than silently deleting or guessing chemistry.

## Route the request

- **Inspect a structure:** run `scripts/validate_pdb.py` first. Check atom count, chains, residue identifiers, positions, and duplicate atom names within residues.
- **Extract chains or a domain:** use `scripts/select_chains_and_residues.py` with explicit `--chain` and/or inclusive `--residue-range CHAIN:START-END`. Use `--dry-run` before writing.
- **Normalize a selected residue:** use `scripts/normalize_ligand_residue.py` only after the residue is uniquely identified. It changes names and preserves the topology graph; it does not parameterize a ligand or infer missing bonds.
- **Protonate, cap, or repair chemistry:** treat Maestro, PyMOL, PDBFixer, OpenFF, or another external tool as an explicit handoff. Revalidate its output instead of assuming the tool preserved IDs and chemistry.

## Required sequence

1. Preserve the original input and establish source structure, virus lineage, chain IDs, residue IDs, and intended molecule.
2. Validate without writing. Resolve absent chains, ambiguous ranges, alternate locations, insertion codes, malformed records, and duplicate names before selection.
3. Run a dry-run selection and review the reported chains, residues, and atom count.
4. Write to a new output path. Revalidate the result and compare the selection against the intended domain or ligand.
5. Perform any external protonation/capping/parameterization only after the coordinate selection is stable. Record the tool, version, and transformations.
6. Hand off the final PDB and its validation report to [system-preparation](../system-preparation/SKILL.md). Record structural identity and transformations through [project-context](../project-context/SKILL.md).

## Safety boundaries

Do not infer protonation, ligand bonds, stereochemistry, residue ranges, or biological identity from a filename. FASTA is sequence evidence, not a coordinate topology; SDF is chemistry evidence, not automatically a PDB-compatible residue. Do not claim a PDB is simulation-ready merely because it parses. Do not overwrite an input by default, and do not run the original repository’s hard-coded curation scripts.

See [data-formats.md](references/data-formats.md), [workflows.md](references/workflows.md), and [troubleshooting.md](references/troubleshooting.md) for contracts and blocked cases.
